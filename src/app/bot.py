from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from src.db.database import start_db
from src.handlers import circles, common


async def run_bot(token: str) -> None:
    await start_db()
    bot = Bot(
        token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_routers(
        common.router,
        circles.router,
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
