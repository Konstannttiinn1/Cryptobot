from __future__ import annotations

from datetime import datetime

from app.constants import COINS_BY_ID, MAX_MESSAGE_LENGTH, TRUNCATED_MESSAGE_NOTICE


def _format_number(value: float, decimals: int) -> str:
    text = f"{value:,.{decimals}f}".replace(",", " ")
    return text


def format_price(price: float | None, currency: str, symbol: str) -> str:
    if price is None:
        return "н/д"

    if currency == "rub":
        if price >= 1000:
            return f"{_format_number(price, 0)} ₽"
        return f"{_format_number(price, 2)} ₽"

    if symbol in {"BTC", "ETH"} or price >= 1:
        return f"${_format_number(price, 2)}"
    return f"${_format_number(price, 4)}"


def format_percent(value: float | None) -> str:
    if value is None:
        return "н/д"
    if abs(value) < 0.1:
        return f"{value:+.2f}%"
    return f"{value:+.1f}%"


def _build_coin_line(coin_id: str, prices: dict, currency: str) -> str | None:
    coin = COINS_BY_ID.get(coin_id)
    if not coin:
        return None
    values = prices.get(coin_id, {})
    price = values.get(currency)
    change = values.get(f"{currency}_24h_change")
    return (
        f"{coin.emoji} {coin.symbol}: {format_price(price, currency, coin.symbol)} | "
        f"{format_percent(change)} за 24ч"
    )


def _finalize_prices_message(title: str, coin_lines: list[str], currency: str) -> str:
    lines = [title, "", *coin_lines]
    lines.extend(
        [
            "",
            f"Валюта: {currency.upper()}",
            f"Обновлено: {datetime.now().strftime('%H:%M')}",
        ]
    )
    return "\n".join(lines)


def build_prices_message(coin_ids: list[str], prices: dict, currency: str, title: str = "📊 Курс сейчас") -> str:
    coin_lines = [
        line
        for coin_id in coin_ids
        if (line := _build_coin_line(coin_id, prices, currency)) is not None
    ]
    message = _finalize_prices_message(title, coin_lines, currency)
    if len(message) <= MAX_MESSAGE_LENGTH:
        return message

    safe_coin_lines: list[str] = []
    for line in coin_lines:
        candidate = _finalize_prices_message(title, [*safe_coin_lines, line, TRUNCATED_MESSAGE_NOTICE], currency)
        if len(candidate) > MAX_MESSAGE_LENGTH:
            break
        safe_coin_lines.append(line)

    return _finalize_prices_message(title, [*safe_coin_lines, TRUNCATED_MESSAGE_NOTICE], currency)
