from math import ceil

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.constants import AVAILABLE_COINS, COINS_PER_PAGE, MAX_SEARCH_RESULTS, SUPPORTED_INTERVALS, Coin


MAIN_REPLY_BUTTONS = {
    "prices": "📊 Курс сейчас",
    "coins": "🪙 Выбрать монеты",
    "currency": "💱 Валюта",
    "interval": "⏱ Интервал",
    "notifications": "🔔 Уведомления",
    "support": "🆘 Поддержка",
}


def main_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📊 Курс сейчас", callback_data="prices:now")],
        [InlineKeyboardButton(text="🪙 Выбрать монеты", callback_data="coins:page:1")],
        [InlineKeyboardButton(text="💱 Валюта", callback_data="menu:currency")],
        [InlineKeyboardButton(text="⏱ Интервал уведомлений", callback_data="menu:interval")],
        [InlineKeyboardButton(text="🔔 Включить уведомления", callback_data="notifications:on")],
        [InlineKeyboardButton(text="🔕 Остановить уведомления", callback_data="notifications:off")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MAIN_REPLY_BUTTONS["prices"]), KeyboardButton(text=MAIN_REPLY_BUTTONS["coins"])],
            [KeyboardButton(text=MAIN_REPLY_BUTTONS["currency"]), KeyboardButton(text=MAIN_REPLY_BUTTONS["interval"])],
            [KeyboardButton(text=MAIN_REPLY_BUTTONS["notifications"]), KeyboardButton(text=MAIN_REPLY_BUTTONS["support"])],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]]
    )


def _coin_button(coin: Coin, selected: set[str], callback_data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=f"{'✅' if coin.coin_id in selected else '⬜'} {coin.symbol} — {coin.name}",
        callback_data=callback_data,
    )


def total_coin_pages() -> int:
    return max(1, ceil(len(AVAILABLE_COINS) / COINS_PER_PAGE))


def normalize_coin_page(page: int) -> int:
    return min(max(page, 1), total_coin_pages())


def coins_for_page(page: int) -> tuple[Coin, ...]:
    normalized_page = normalize_coin_page(page)
    start = (normalized_page - 1) * COINS_PER_PAGE
    end = start + COINS_PER_PAGE
    return AVAILABLE_COINS[start:end]


def coins_keyboard(selected_coin_ids: list[str], page: int = 1) -> InlineKeyboardMarkup:
    selected = set(selected_coin_ids)
    normalized_page = normalize_coin_page(page)
    pages = total_coin_pages()
    rows = [
        [_coin_button(coin, selected, f"coin:{normalized_page}:{coin.coin_id}")]
        for coin in coins_for_page(normalized_page)
    ]

    previous_page = normalized_page - 1 if normalized_page > 1 else pages
    next_page = normalized_page + 1 if normalized_page < pages else 1
    if pages > 1:
        rows.append(
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data=f"coins:page:{previous_page}"),
                InlineKeyboardButton(text="▶️ Далее", callback_data=f"coins:page:{next_page}"),
            ]
        )
    rows.append([InlineKeyboardButton(text="🔎 Поиск", callback_data="coins:search")])
    rows.append([InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def search_results_keyboard(selected_coin_ids: list[str], coins: list[Coin]) -> InlineKeyboardMarkup:
    selected = set(selected_coin_ids)
    rows = [
        [_coin_button(coin, selected, f"search_coin:{coin.coin_id}")]
        for coin in coins[:MAX_SEARCH_RESULTS]
    ]
    rows.extend(
        [
            [InlineKeyboardButton(text="🔎 Новый поиск", callback_data="coins:search")],
            [InlineKeyboardButton(text="⬅️ К списку монет", callback_data="coins:page:1")],
            [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:main")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def currency_keyboard(selected_currency: str) -> InlineKeyboardMarkup:
    labels = {"rub": "RUB — рубли", "usd": "USD — доллары"}
    rows = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if selected_currency == currency else '⬜'} {label}",
                callback_data=f"currency:{currency}",
            )
        ]
        for currency, label in labels.items()
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def interval_keyboard(selected_minutes: int) -> InlineKeyboardMarkup:
    def label(minutes: int) -> str:
        return "1 час" if minutes == 60 else f"{minutes} минут"

    rows = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if selected_minutes == minutes else '⬜'} {label(minutes)}",
                callback_data=f"interval:{minutes}",
            )
        ]
        for minutes in SUPPORTED_INTERVALS
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def notifications_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Включить уведомления", callback_data="notifications:on")],
            [InlineKeyboardButton(text="🔕 Остановить уведомления", callback_data="notifications:off")],
            [InlineKeyboardButton(text="⬅️ В меню", callback_data="menu:main")],
        ]
    )


def support_url_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть поддержку", url=url)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")],
        ]
    )
