from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    bot_token: str = ""
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/memorio"
    )
    webapp_url: str = "http://localhost:8000"
    webapp_host: str = "0.0.0.0"
    webapp_port: int = 8000
    jwt_secret: str = "memorio-dev-secret"
    jwt_ttl_seconds: int = 86400
    chat_id: int | None = Field(default=None, alias="CHAT_ID")
    admin_id: int | None = None

    class Config:
        env_file = ".env"
