from __future__ import annotations

import logging
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app import database as db
from app.config import Config
from app.constants import AVAILABLE_COINS, COINS_BY_ID, Coin
from app.crypto_api import CryptoAPIError, fetch_prices
from app.formatters import build_prices_message
from app.keyboards import (
    MAIN_REPLY_BUTTONS,
    back_keyboard,
    coins_keyboard,
    currency_keyboard,
    interval_keyboard,
    main_menu,
    main_reply_keyboard,
    search_results_keyboard,
    support_url_keyboard,
    total_coin_pages,
    normalize_coin_page,
)

logger = logging.getLogger(__name__)
router = Router()
_config: Config | None = None
_last_search_queries: dict[int, str] = {}

START_TEXT = "Привет! Я могу присылать актуальный курс выбранных криптовалют."
CURRENCY_TEXT = "💱 Выберите валюту отображения:"
INTERVAL_TEXT = "⏱ Как часто присылать уведомления?"
NOTIFICATIONS_TEXT = "⏱ Выберите интервал уведомлений. После выбора интервала уведомления включатся автоматически."
NO_COINS_TEXT = "Вы пока не выбрали монеты. Откройте раздел «Выбрать монеты»."
API_ERROR_TEXT = "Не удалось получить курс. Попробуйте позже."
SEARCH_PROMPT_TEXT = "Введите название или тикер монеты. Например: BTC, GRAM, Ethereum"
SEARCH_RESULTS_TEXT = "🔎 Результаты поиска:"
SEARCH_NOT_FOUND_TEXT = "Ничего не найдено. Попробуйте другой тикер или название."
MAX_SELECTED_COINS_ALERT = "Можно выбрать максимум {limit} монет."
MANUAL_PRICE_COOLDOWN_SECONDS = 60
PRICE_COOLDOWN_TEXT = "⏳ Курс сейчас можно запрашивать не чаще одного раза в минуту. Попробуйте через {seconds} сек."


class CoinSearch(StatesGroup):
    waiting_for_query = State()


def setup_router(config: Config) -> Router:
    global _config
    _config = config
    return router


def get_config() -> Config:
    if _config is None:
        raise RuntimeError("Handlers config is not initialized")
    return _config


def build_coins_text(selected_count: int, page: int = 1) -> str:
    normalized_page = normalize_coin_page(page)
    return (
        "🪙 Выберите монеты для отслеживания:\n\n"
        f"Выбрано: {selected_count}/{get_config().max_selected_coins}\n\n"
        f"Страница {normalized_page}/{total_coin_pages()}"
    )


def search_available_coins(query: str) -> list[Coin]:
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return []
    return [
        coin
        for coin in AVAILABLE_COINS
        if normalized_query in coin.symbol.casefold()
        or normalized_query in coin.name.casefold()
        or normalized_query in coin.coin_id.casefold()
        or any(normalized_query in alias.casefold() for alias in coin.aliases)
    ]


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


async def show_main_menu_message(message: Message) -> None:
    if not message.from_user:
        return
    await db.create_user_if_not_exists(message.from_user.id)
    await message.answer(START_TEXT, reply_markup=main_reply_keyboard())
    await message.answer("Главное меню:", reply_markup=main_menu())


async def check_manual_price_cooldown(user_id: int) -> int:
    settings = await db.get_user_settings(user_id)
    last_requested_at = settings.get("last_manual_price_at") if settings else None
    if not last_requested_at:
        return 0
    try:
        last_requested = datetime.fromisoformat(last_requested_at)
    except ValueError:
        return 0
    elapsed = (datetime.now(timezone.utc) - last_requested).total_seconds()
    remaining = MANUAL_PRICE_COOLDOWN_SECONDS - int(elapsed)
    return max(0, remaining)


async def show_prices_message(message: Message) -> None:
    if not message.from_user:
        return
    cooldown_seconds = await check_manual_price_cooldown(message.from_user.id)
    if cooldown_seconds > 0:
        await message.answer(PRICE_COOLDOWN_TEXT.format(seconds=cooldown_seconds), reply_markup=main_reply_keyboard())
        return
    coin_ids = await db.get_user_coins(message.from_user.id)
    if not coin_ids:
        await message.answer(NO_COINS_TEXT, reply_markup=main_reply_keyboard())
        return

    settings = await db.get_user_settings(message.from_user.id)
    try:
        prices = await fetch_prices(coin_ids, get_config())
        await db.upsert_prices_cache(prices)
    except CryptoAPIError:
        await message.answer(API_ERROR_TEXT, reply_markup=main_reply_keyboard())
        return

    await db.update_last_manual_price_at(message.from_user.id)
    text = build_prices_message(coin_ids, prices, settings["currency"])
    await message.answer(text, reply_markup=main_reply_keyboard())


async def show_settings_message(message: Message) -> None:
    if not message.from_user:
        return
    settings = await db.get_user_settings(message.from_user.id)
    coin_ids = await db.get_user_coins(message.from_user.id)
    text = (
        "⚙️ Настройки\n\n"
        f"Монет выбрано: {len(coin_ids)}/{get_config().max_selected_coins}\n"
        f"Валюта: {settings['currency'].upper()}\n"
        f"Интервал: {settings['interval_minutes']} минут\n"
        f"Уведомления: {'включены' if settings['notifications_enabled'] else 'выключены'}"
    )
    await message.answer(text, reply_markup=main_reply_keyboard())
    await message.answer("Разделы настроек:", reply_markup=main_menu())


async def show_coins_list_message(message: Message, page: int = 1) -> None:
    if not message.from_user:
        return
    coins = await db.get_user_coins(message.from_user.id)
    await message.answer(
        build_coins_text(len(coins), page),
        reply_markup=coins_keyboard(coins, page),
    )


async def toggle_coin_for_user(user_id: int, coin_id: str) -> tuple[list[str], bool]:
    selected = await db.get_user_coins(user_id)
    if coin_id not in selected and len(selected) >= get_config().max_selected_coins:
        return selected, False
    selected = await db.toggle_user_coin(user_id, coin_id)
    return selected, True


@router.message(Command("start", "menu"))
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_main_menu_message(message)


@router.message(Command("price"))
async def price_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_prices_message(message)


@router.message(Command("coins"))
async def coins_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_coins_list_message(message)


@router.message(Command("settings"))
async def settings_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_settings_message(message)


@router.message(Command("hide"))
async def hide_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Клавиатура скрыта. Чтобы открыть меню снова, напишите /menu.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(Command("stop"))
async def stop_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not message.from_user:
        return
    await db.set_notifications_enabled(message.from_user.id, False)
    await message.answer("🔕 Уведомления остановлены.", reply_markup=main_reply_keyboard())


@router.message(F.text == MAIN_REPLY_BUTTONS["prices"])
async def prices_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_prices_message(message)


@router.message(F.text == MAIN_REPLY_BUTTONS["coins"])
async def coins_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    await show_coins_list_message(message)


@router.message(F.text == MAIN_REPLY_BUTTONS["currency"])
async def currency_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    settings = await db.get_user_settings(message.from_user.id)
    await message.answer(CURRENCY_TEXT, reply_markup=currency_keyboard(settings["currency"]))


@router.message(F.text == MAIN_REPLY_BUTTONS["notifications"])
async def notifications_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    settings = await db.get_user_settings(message.from_user.id)
    await message.answer(NOTIFICATIONS_TEXT, reply_markup=interval_keyboard(settings["interval_minutes"]))


@router.message(F.text == MAIN_REPLY_BUTTONS["support"])
async def support_reply(message: Message, state: FSMContext) -> None:
    await state.clear()
    config = get_config()
    if config.support_url:
        await message.answer("🆘 Поддержка", reply_markup=support_url_keyboard(config.support_url))
    else:
        await message.answer("Ссылка на поддержку пока не настроена.", reply_markup=main_reply_keyboard())


@router.callback_query(F.data == "menu:main")
async def show_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.from_user:
        await db.create_user_if_not_exists(callback.from_user.id)
    await safe_edit(callback, START_TEXT, reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "menu:coins")
@router.callback_query(F.data.startswith("coins:page:"))
async def show_coins_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    page = 1
    if callback.data and callback.data.startswith("coins:page:"):
        try:
            page = int(callback.data.rsplit(":", 1)[1])
        except ValueError:
            page = 1
    coins = await db.get_user_coins(callback.from_user.id)
    await safe_edit(callback, build_coins_text(len(coins), page), reply_markup=coins_keyboard(coins, page))
    await callback.answer()


@router.callback_query(F.data == "coins:search")
async def start_coin_search(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CoinSearch.waiting_for_query)
    await safe_edit(callback, SEARCH_PROMPT_TEXT, reply_markup=search_results_keyboard([], []))
    await callback.answer()


@router.message(CoinSearch.waiting_for_query)
async def process_coin_search(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not message.from_user or not message.text:
        return
    query = message.text.strip()
    results = search_available_coins(query)
    _last_search_queries[message.from_user.id] = query
    selected = await db.get_user_coins(message.from_user.id)
    if not results:
        await message.answer(
            SEARCH_NOT_FOUND_TEXT,
            reply_markup=search_results_keyboard(selected, []),
        )
        return
    await message.answer(
        SEARCH_RESULTS_TEXT,
        reply_markup=search_results_keyboard(selected, results),
    )


@router.callback_query(F.data.startswith("coin:"))
async def toggle_coin(callback: CallbackQuery) -> None:
    page = 1
    coin_id = ""
    if callback.data:
        parts = callback.data.split(":", 2)
        if len(parts) == 3:
            try:
                page = int(parts[1])
            except ValueError:
                page = 1
            coin_id = parts[2]
        elif len(parts) == 2:
            coin_id = parts[1]

    selected, changed = await toggle_coin_for_user(callback.from_user.id, coin_id)
    if not changed:
        await callback.answer(
            MAX_SELECTED_COINS_ALERT.format(limit=get_config().max_selected_coins),
            show_alert=True,
        )
        return

    await safe_edit(callback, build_coins_text(len(selected), page), reply_markup=coins_keyboard(selected, page))
    await callback.answer()


@router.callback_query(F.data.startswith("search_coin:"))
async def toggle_search_coin(callback: CallbackQuery) -> None:
    coin_id = callback.data.split(":", 1)[1] if callback.data else ""
    selected, changed = await toggle_coin_for_user(callback.from_user.id, coin_id)
    if not changed:
        await callback.answer(
            MAX_SELECTED_COINS_ALERT.format(limit=get_config().max_selected_coins),
            show_alert=True,
        )
        return

    query = _last_search_queries.get(callback.from_user.id, "")
    results = search_available_coins(query)
    await safe_edit(callback, SEARCH_RESULTS_TEXT, reply_markup=search_results_keyboard(selected, results))
    await callback.answer()


@router.callback_query(F.data == "menu:currency")
async def show_currency_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
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
async def show_interval_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    settings = await db.get_user_settings(callback.from_user.id)
    await safe_edit(callback, NOTIFICATIONS_TEXT, reply_markup=interval_keyboard(settings["interval_minutes"]))
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
    await safe_edit(callback, NOTIFICATIONS_TEXT, reply_markup=interval_keyboard(settings["interval_minutes"]))
    await callback.answer("Уведомления включены")


@router.callback_query(F.data == "prices:now")
async def show_prices_now(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    cooldown_seconds = await check_manual_price_cooldown(callback.from_user.id)
    if cooldown_seconds > 0:
        await safe_edit(callback, PRICE_COOLDOWN_TEXT.format(seconds=cooldown_seconds), reply_markup=back_keyboard())
        await callback.answer()
        return

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

    await db.update_last_manual_price_at(callback.from_user.id)
    text = build_prices_message(coin_ids, prices, settings["currency"])
    await safe_edit(callback, text, reply_markup=back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "notifications:on")
async def enable_notifications(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
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
async def disable_notifications(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await db.set_notifications_enabled(callback.from_user.id, False)
    await safe_edit(callback, "🔕 Уведомления остановлены.", reply_markup=back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    config = get_config()
    if config.support_url:
        await safe_edit(callback, "🆘 Поддержка", reply_markup=support_url_keyboard(config.support_url))
    else:
        await safe_edit(callback, "Ссылка на поддержку пока не настроена.", reply_markup=back_keyboard())
    await callback.answer()
