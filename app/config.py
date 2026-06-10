from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os


load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    coingecko_api_key: str | None
    support_url: str | None
    database_path: str = str(Path("bot.db"))


def get_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN не задан. Добавьте токен Telegram-бота в .env")

    api_key = os.getenv("COINGECKO_API_KEY", "").strip() or None
    support_url = os.getenv("SUPPORT_URL", "").strip() or None
    database_path = os.getenv("DATABASE_PATH", "bot.db").strip() or "bot.db"

    return Config(
        bot_token=token,
        coingecko_api_key=api_key,
        support_url=support_url,
        database_path=database_path,
    )
