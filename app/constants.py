from dataclasses import dataclass


@dataclass(frozen=True)
class Coin:
    coin_id: str
    symbol: str
    name: str
    emoji: str


AVAILABLE_COINS: tuple[Coin, ...] = (
    Coin("bitcoin", "BTC", "Bitcoin", "₿"),
    Coin("the-open-network", "TON", "Toncoin", "🔵"),
    Coin("ethereum", "ETH", "Ethereum", "♦️"),
    Coin("solana", "SOL", "Solana", "🟣"),
    Coin("binancecoin", "BNB", "BNB", "🟡"),
    Coin("ripple", "XRP", "XRP", "✖️"),
    Coin("dogecoin", "DOGE", "Dogecoin", "🐶"),
    Coin("tron", "TRX", "Tron", "🔺"),
    Coin("tether", "USDT", "Tether", "💵"),
    Coin("notcoin", "NOT", "Notcoin", "🎮"),
)

COINS_BY_ID = {coin.coin_id: coin for coin in AVAILABLE_COINS}
DEFAULT_COIN_IDS = ("bitcoin", "the-open-network", "tether")
SUPPORTED_CURRENCIES = ("rub", "usd")
SUPPORTED_INTERVALS = (5, 10, 15, 30, 60)
MAX_SELECTED_COINS = 20
MAX_MESSAGE_LENGTH = 3900
TRUNCATED_MESSAGE_NOTICE = "Часть монет не показана из-за ограничения длины сообщения."
