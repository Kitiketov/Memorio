from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)


LOCATION_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="Поделиться геопозицией",
                request_location=True,
            )
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def webapp_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть карту",
                    web_app=WebAppInfo(url=url),
                )
            ]
        ]
    )


def url_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть карту",
                    url=url,
                )
            ]
        ]
    )
