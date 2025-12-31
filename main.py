import asyncio

import uvicorn

from src.app.bot import run_bot
from src.config import settings
from src.webapp.app import app as web_app


async def run_webapp() -> None:
    config = uvicorn.Config(
        web_app,
        host=settings.webapp_host,
        port=settings.webapp_port,
        log_level="info",
        loop="asyncio",
        lifespan="on",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    await asyncio.gather(
        run_bot(settings.bot_token),
        run_webapp(),
    )


if __name__ == "__main__":
    asyncio.run(main())
