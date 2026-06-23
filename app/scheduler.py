from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app import database as db
from app.config import Config
from app.crypto_api import CryptoAPIError, fetch_prices
from app.formatters import build_prices_message

logger = logging.getLogger(__name__)
API_ERROR_TEXT = "Не удалось получить курс. Попробуйте позже."


async def scheduler_loop(bot: Bot, config: Config, stop_event: asyncio.Event) -> None:
    """Check due users every minute and send scheduled rate notifications."""
    while not stop_event.is_set():
        try:
            await send_due_notifications(bot, config)
        except Exception:
            logger.exception("Unexpected scheduler error")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=60)
        except TimeoutError:
            continue


async def send_due_notifications(bot: Bot, config: Config) -> None:
    users = await db.get_users_due_for_notification(datetime.now(timezone.utc))
    if not users:
        return

    user_coin_ids: dict[int, list[str]] = {}
    all_coin_ids: set[str] = set()
    for user in users:
        user_id = user["user_id"]
        coin_ids = await db.get_user_coins(user_id)
        if not coin_ids:
            logger.info("Skip notification for %s: no selected coins", user_id)
            continue
        user_coin_ids[user_id] = coin_ids
        all_coin_ids.update(coin_ids)

    prices: dict = {}
    fetch_failed = False
    if all_coin_ids:
        try:
            prices = await fetch_prices(sorted(all_coin_ids), config)
            await db.upsert_prices_cache(prices)
        except CryptoAPIError:
            fetch_failed = True

    for user in users:
        user_id = user["user_id"]
        coin_ids = user_coin_ids.get(user_id)
        if not coin_ids:
            continue

        if fetch_failed:
            text = API_ERROR_TEXT
        else:
            text = build_prices_message(coin_ids, prices, user["currency"], title="📊 Обновление курса")

        try:
            await bot.send_message(user_id, text)
            await db.update_last_sent_at(user_id)
        except TelegramAPIError:
            logger.exception("Failed to send notification to user %s", user_id)
