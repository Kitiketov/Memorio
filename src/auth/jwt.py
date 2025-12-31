from __future__ import annotations

import base64
import hmac
import json
import time
from hashlib import sha256
from typing import Any


class TokenError(ValueError):
    pass


def create_token(user_id: int, secret: str, ttl_seconds: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "exp": int(time.time()) + ttl_seconds,
    }
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(secret.encode(), signing_input, sha256).digest()
    signature_b64 = _b64url_encode(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_token(token: str, secret: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise TokenError("Invalid token format") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(secret.encode(), signing_input, sha256).digest()
    if not _compare_signatures(signature_b64, expected_sig):
        raise TokenError("Invalid token signature")

    header = _decode_json(header_b64)
    if header.get("alg") != "HS256":
        raise TokenError("Unsupported algorithm")

    payload = _decode_json(payload_b64)
    exp = payload.get("exp")
    if isinstance(exp, int) and exp < int(time.time()):
        raise TokenError("Token expired")
    return payload


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _decode_json(data: str) -> dict[str, Any]:
    try:
        raw = _b64url_decode(data)
        return json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise TokenError("Invalid token payload") from exc


def _compare_signatures(signature_b64: str, expected: bytes) -> bool:
    try:
        actual = _b64url_decode(signature_b64)
    except ValueError:
        return False
    return hmac.compare_digest(actual, expected)
