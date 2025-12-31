from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from src.auth import create_token
from src.config import settings
from src.keyboards import webapp_keyboard
from src.texts import MAP_LOCAL_TEXT, MAP_OPEN_TEXT, START_MESSAGE, WEBAPP_URL_MISSING


router = Router(name=__name__)


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(START_MESSAGE)


@router.message(Command("map"))
async def open_map(message: Message) -> None:
    base_url = settings.webapp_url.strip().rstrip("/")
    if not base_url:
        await message.answer(WEBAPP_URL_MISSING)
        return
    token = create_token(
        message.from_user.id,
        settings.jwt_secret,
        settings.jwt_ttl_seconds,
    )
    url = f"{base_url}/{message.from_user.id}?token={token}"

    if base_url.startswith("https://"):
        keyboard = webapp_keyboard(url)
        await message.answer(
            MAP_OPEN_TEXT,
            reply_markup=keyboard,
        )
        return

    await message.answer(
        MAP_LOCAL_TEXT.format(url=url)
    )
