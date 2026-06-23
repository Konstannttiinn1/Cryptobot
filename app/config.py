from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

from app.constants import MAX_SELECTED_COINS


load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    coingecko_api_key: str | None
    support_url: str | None
    database_path: str = str(Path("bot.db"))
    max_selected_coins: int = MAX_SELECTED_COINS


def _get_positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


def get_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN не задан. Добавьте токен Telegram-бота в .env")

    api_key = os.getenv("COINGECKO_API_KEY", "").strip() or None
    support_url = os.getenv("SUPPORT_URL", "").strip() or None
    database_path = os.getenv("DATABASE_PATH", "bot.db").strip() or "bot.db"
    max_selected_coins = _get_positive_int("MAX_SELECTED_COINS", MAX_SELECTED_COINS)

    return Config(
        bot_token=token,
        coingecko_api_key=api_key,
        support_url=support_url,
        database_path=database_path,
        max_selected_coins=max_selected_coins,
    )
