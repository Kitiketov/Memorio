from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from src.db.crud import create_circle
from src.db.database import SessionLocal
from src.db.models import CircleRecord
from src.keyboards import LOCATION_KEYBOARD
from src.states import CircleStates
from src.texts import (
    ASK_LOCATION_TEXT,
    MISSING_MEDIA_TEXT,
    NEED_LOCATION_TEXT,
    NEED_MEDIA_TEXT,
    SAVED_TEXT,
)


router = Router(name=__name__)


async def start_media_flow(
    message: Message,
    state: FSMContext,
    media_id: str,
    media_type: str,
) -> None:
    await state.update_data(
        media_id=media_id,
        recorded_at=message.date,
        media_type=media_type,
    )
    await message.answer(
        ASK_LOCATION_TEXT,
        reply_markup=LOCATION_KEYBOARD,
    )
    await state.set_state(CircleStates.waiting_location)


@router.message(F.video_note)
async def handle_video_note(message: Message, state: FSMContext) -> None:
    await start_media_flow(
        message,
        state,
        media_id=message.video_note.file_id,
        media_type="video_note",
    )


@router.message(F.video)
async def handle_video(message: Message, state: FSMContext) -> None:
    await start_media_flow(
        message,
        state,
        media_id=message.video.file_id,
        media_type="video",
    )


@router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext) -> None:
    photo = message.photo[-1]
    await start_media_flow(
        message,
        state,
        media_id=photo.file_id,
        media_type="photo",
    )


@router.message(CircleStates.waiting_location, F.location)
async def handle_location(message: Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    media_id = state_data.get("media_id")
    record_date = state_data.get("recorded_at", message.date)
    record_type = state_data.get("media_type", "video_note")

    if not media_id:
        await message.answer(
            MISSING_MEDIA_TEXT,
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()
        return

    location = {
        "lat": message.location.latitude,
        "lon": message.location.longitude,
    }
    username = message.from_user.username
    if username:
        display_name = f"@{username}"
    else:
        display_name = (
            message.from_user.full_name or f"User {message.from_user.id}"
        )
    record = CircleRecord(
        user_id=message.from_user.id,
        data=record_date,
        location=location,
        type=record_type,
        media_id=media_id,
        username=display_name,
        description="",
    )
    async with SessionLocal() as session:
        await create_circle(session, record)

    await state.clear()
    await message.answer(
        SAVED_TEXT,
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(CircleStates.waiting_location)
async def waiting_location_only(message: Message) -> None:
    await message.answer(
        NEED_LOCATION_TEXT,
        reply_markup=LOCATION_KEYBOARD,
    )


@router.message(F.location)
async def location_without_video(message: Message) -> None:
    await message.answer(NEED_MEDIA_TEXT)
