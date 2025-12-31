from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlencode

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.auth import TokenError, verify_token
from src.config import settings
from src.db.crud import delete_circle, get_circle, list_circles
from src.db.database import get_session, start_db


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
TELEGRAM_API_BASE = "https://api.telegram.org"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await start_db()
    async with httpx.AsyncClient(timeout=30.0) as client:
        app.state.http_client = client
        yield


app = FastAPI(lifespan=lifespan)


class DescriptionPayload(BaseModel):
    description: str = Field(default="", max_length=2000)


@app.get("/", response_class=PlainTextResponse)
async def index() -> PlainTextResponse:
    return PlainTextResponse("Use your personal link /<user_id>?token=...")


@app.get("/{user_id}", response_class=HTMLResponse)
async def user_index(
    request: Request,
    user_id: int,
    token: str | None = None,
) -> HTMLResponse:
    _validate_token(token, user_id)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user_id": user_id,
            "token": token,
        },
    )


@app.get("/api/markers")
async def markers(
    user_id: int,
    token: str,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    _validate_token(token, user_id)
    records = await list_circles(session, user_id)
    payload = []
    updated = False
    auth_query = urlencode({"user_id": user_id, "token": token})
    for record in records:
        username = record.username
        needs_lookup = not username or not username.startswith("@")
        if needs_lookup:
            resolved = await _fetch_telegram_username(record.user_id)
            if resolved and resolved != record.username:
                record.username = resolved
                updated = True
            username = resolved or username
        if not username:
            username = f"User {record.user_id}"
        payload.append(
            {
                "id": record.id,
                "user_id": record.user_id,
                "data": record.data.isoformat() if record.data else None,
                "location": record.location,
                "type": record.type,
                "media_id": record.media_id,
                "username": username,
                "description": record.description,
                "media_url": f"/api/media/{record.id}?{auth_query}",
            }
        )
    if updated:
        await session.commit()
    return payload


@app.delete("/api/markers/{record_id}")
async def delete_marker(
    record_id: int,
    user_id: int,
    token: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    _validate_token(token, user_id)
    record = await get_circle(session, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    if record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden.")
    await delete_circle(session, record)
    return {"status": "ok"}


@app.patch("/api/markers/{record_id}/description")
async def update_description(
    record_id: int,
    payload: DescriptionPayload,
    user_id: int,
    token: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    _validate_token(token, user_id)
    record = await get_circle(session, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    if record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden.")
    record.description = payload.description.strip()
    await session.commit()
    return {"status": "ok", "description": record.description}


@app.get("/api/media/{record_id}")
async def media(
    record_id: int,
    user_id: int,
    token: str,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    _validate_token(token, user_id)
    if not settings.bot_token:
        raise HTTPException(status_code=500, detail="Bot token is not configured.")

    record = await get_circle(session, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Media not found.")
    if record.user_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden.")

    file_path = await _get_file_path(record.media_id)
    file_url = f"{TELEGRAM_API_BASE}/file/bot{settings.bot_token}/{file_path}"
    response = await _fetch_file(file_url)
    content_type = response.headers.get("content-type", "video/mp4")
    return StreamingResponse(response.aiter_bytes(), media_type=content_type)


async def _get_file_path(file_id: str) -> str:
    url = f"{TELEGRAM_API_BASE}/bot{settings.bot_token}/getFile"
    response = await _fetch_file(url, params={"file_id": file_id})
    payload = response.json()
    if not payload.get("ok"):
        raise HTTPException(status_code=502, detail="Telegram getFile failed.")
    return payload["result"]["file_path"]


async def _fetch_telegram_username(user_id: int) -> str | None:
    if not settings.bot_token:
        return None
    url = f"{TELEGRAM_API_BASE}/bot{settings.bot_token}/getChat"
    payload = await _fetch_json(url, params={"chat_id": user_id})
    if not payload or not payload.get("ok"):
        return None
    result = payload.get("result", {})
    username = result.get("username")
    if username:
        return f"@{username}" if not username.startswith("@") else username
    first = result.get("first_name") or ""
    last = result.get("last_name") or ""
    full = " ".join(part for part in (first, last) if part).strip()
    return full or None


async def _fetch_file(url: str, params: dict | None = None) -> httpx.Response:
    client: httpx.AsyncClient = app.state.http_client
    response = await client.get(url, params=params)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Telegram API error.")
    return response


async def _fetch_json(url: str, params: dict | None = None) -> dict | None:
    client: httpx.AsyncClient = app.state.http_client
    try:
        response = await client.get(url, params=params)
    except httpx.HTTPError:
        return None
    if response.status_code >= 400:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def _validate_token(token: str | None, user_id: int) -> None:
    if not token:
        raise HTTPException(status_code=401, detail="Token required.")
    try:
        payload = verify_token(token, settings.jwt_secret)
    except TokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    if str(payload.get("sub")) != str(user_id):
        raise HTTPException(status_code=401, detail="Invalid token subject.")
