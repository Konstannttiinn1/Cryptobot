from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.constants import AVAILABLE_COINS, SUPPORTED_INTERVALS


def main_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📊 Курс сейчас", callback_data="prices:now")],
        [InlineKeyboardButton(text="🪙 Выбрать монеты", callback_data="menu:coins")],
        [InlineKeyboardButton(text="💱 Валюта", callback_data="menu:currency")],
        [InlineKeyboardButton(text="⏱ Интервал уведомлений", callback_data="menu:interval")],
        [InlineKeyboardButton(text="🔔 Включить уведомления", callback_data="notifications:on")],
        [InlineKeyboardButton(text="🔕 Остановить уведомления", callback_data="notifications:off")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]]
    )


def coins_keyboard(selected_coin_ids: list[str]) -> InlineKeyboardMarkup:
    selected = set(selected_coin_ids)
    rows = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if coin.coin_id in selected else '⬜'} {coin.symbol} — {coin.name}",
                callback_data=f"coin:{coin.coin_id}",
            )
        ]
        for coin in AVAILABLE_COINS
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")])
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


def support_url_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть поддержку", url=url)],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")],
        ]
    )
