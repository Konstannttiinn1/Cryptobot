from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.config import Config
from app import database as db
from app.constants import COINS_BY_ID
from app.crypto_api import CryptoAPIError, fetch_prices
from app.formatters import build_prices_message
from app.keyboards import (
    back_keyboard,
    coins_keyboard,
    currency_keyboard,
    interval_keyboard,
    main_menu,
    support_url_keyboard,
)

logger = logging.getLogger(__name__)
router = Router()
_config: Config | None = None

START_TEXT = "Привет! Я могу присылать актуальный курс выбранных криптовалют."
CURRENCY_TEXT = "💱 Выберите валюту отображения:"
INTERVAL_TEXT = "⏱ Как часто присылать уведомления?"
NO_COINS_TEXT = "Вы пока не выбрали монеты. Откройте раздел «Выбрать монеты»."
API_ERROR_TEXT = "Не удалось получить курс. Попробуйте позже."
MAX_SELECTED_COINS_ALERT = "Можно выбрать максимум {limit} монет."


def build_coins_text(selected_count: int) -> str:
    return (
        "🪙 Выберите монеты для отслеживания:\n\n"
        f"Выбрано: {selected_count}/{get_config().max_selected_coins}"
    )


def setup_router(config: Config) -> Router:
    global _config
    _config = config
    return router


def get_config() -> Config:
    if _config is None:
        raise RuntimeError("Handlers config is not initialized")
    return _config


async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    try:
        if callback.message:
            await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        # Старые inline-кнопки или попытка отредактировать сообщение тем же содержимым
        # не должны ломать сценарий пользователя.
        logger.debug("Cannot edit message: %s", exc)
        if callback.message:
            await callback.message.answer(text, reply_markup=reply_markup)


@router.message(CommandStart())
async def start(message: Message) -> None:
    if not message.from_user:
        return
    await db.create_user_if_not_exists(message.from_user.id)
    await message.answer(START_TEXT, reply_markup=main_menu())


@router.callback_query(F.data == "menu:main")
async def show_main_menu(callback: CallbackQuery) -> None:
    if callback.from_user:
        await db.create_user_if_not_exists(callback.from_user.id)
    await safe_edit(callback, START_TEXT, reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "menu:coins")
async def show_coins_menu(callback: CallbackQuery) -> None:
    coins = await db.get_user_coins(callback.from_user.id)
    await safe_edit(callback, build_coins_text(len(coins)), reply_markup=coins_keyboard(coins))
    await callback.answer()


@router.callback_query(F.data.startswith("coin:"))
async def toggle_coin(callback: CallbackQuery) -> None:
    coin_id = callback.data.split(":", 1)[1] if callback.data else ""
    selected = await db.get_user_coins(callback.from_user.id)

    if coin_id not in selected and len(selected) >= get_config().max_selected_coins:
        await callback.answer(
            MAX_SELECTED_COINS_ALERT.format(limit=get_config().max_selected_coins),
            show_alert=True,
        )
        return

    selected = await db.toggle_user_coin(callback.from_user.id, coin_id)
    await safe_edit(callback, build_coins_text(len(selected)), reply_markup=coins_keyboard(selected))
    await callback.answer()


@router.callback_query(F.data == "menu:currency")
async def show_currency_menu(callback: CallbackQuery) -> None:
    settings = await db.get_user_settings(callback.from_user.id)
    await safe_edit(callback, CURRENCY_TEXT, reply_markup=currency_keyboard(settings["currency"]))
    await callback.answer()


@router.callback_query(F.data.startswith("currency:"))
async def choose_currency(callback: CallbackQuery) -> None:
    currency = callback.data.split(":", 1)[1] if callback.data else "rub"
    await db.set_currency(callback.from_user.id, currency)
    settings = await db.get_user_settings(callback.from_user.id)
    await safe_edit(callback, CURRENCY_TEXT, reply_markup=currency_keyboard(settings["currency"]))
    await callback.answer("Валюта обновлена")


@router.callback_query(F.data == "menu:interval")
async def show_interval_menu(callback: CallbackQuery) -> None:
    settings = await db.get_user_settings(callback.from_user.id)
    await safe_edit(callback, INTERVAL_TEXT, reply_markup=interval_keyboard(settings["interval_minutes"]))
    await callback.answer()


@router.callback_query(F.data.startswith("interval:"))
async def choose_interval(callback: CallbackQuery) -> None:
    raw_minutes = callback.data.split(":", 1)[1] if callback.data else "5"
    try:
        minutes = int(raw_minutes)
    except ValueError:
        minutes = 5
    await db.set_interval(callback.from_user.id, minutes)
    settings = await db.get_user_settings(callback.from_user.id)
    await safe_edit(callback, INTERVAL_TEXT, reply_markup=interval_keyboard(settings["interval_minutes"]))
    await callback.answer("Интервал обновлен")


@router.callback_query(F.data == "prices:now")
async def show_prices_now(callback: CallbackQuery) -> None:
    coin_ids = await db.get_user_coins(callback.from_user.id)
    if not coin_ids:
        await safe_edit(callback, NO_COINS_TEXT, reply_markup=back_keyboard())
        await callback.answer()
        return

    settings = await db.get_user_settings(callback.from_user.id)
    try:
        prices = await fetch_prices(coin_ids, get_config())
        await db.upsert_prices_cache(prices)
    except CryptoAPIError:
        await safe_edit(callback, API_ERROR_TEXT, reply_markup=back_keyboard())
        await callback.answer()
        return

    text = build_prices_message(coin_ids, prices, settings["currency"])
    await safe_edit(callback, text, reply_markup=back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "notifications:on")
async def enable_notifications(callback: CallbackQuery) -> None:
    coin_ids = await db.get_user_coins(callback.from_user.id)
    if not coin_ids:
        await safe_edit(callback, "Сначала выберите хотя бы одну монету.", reply_markup=back_keyboard())
        await callback.answer()
        return

    await db.set_notifications_enabled(callback.from_user.id, True)
    settings = await db.get_user_settings(callback.from_user.id)
    symbols = [COINS_BY_ID[coin_id].symbol for coin_id in coin_ids if coin_id in COINS_BY_ID]
    text = (
        "🔔 Уведомления включены.\n\n"
        f"Монеты: {', '.join(symbols)}\n"
        f"Валюта: {settings['currency'].upper()}\n"
        f"Интервал: {settings['interval_minutes']} минут"
    )
    await safe_edit(callback, text, reply_markup=back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "notifications:off")
async def disable_notifications(callback: CallbackQuery) -> None:
    await db.set_notifications_enabled(callback.from_user.id, False)
    await safe_edit(callback, "🔕 Уведомления остановлены.", reply_markup=back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery) -> None:
    config = get_config()
    if config.support_url:
        await safe_edit(callback, "🆘 Поддержка", reply_markup=support_url_keyboard(config.support_url))
    else:
        await safe_edit(callback, "Ссылка на поддержку пока не настроена.", reply_markup=back_keyboard())
    await callback.answer()
