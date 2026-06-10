from __future__ import annotations

import logging

import aiohttp

from app.config import Config

logger = logging.getLogger(__name__)

COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"


class CryptoAPIError(Exception):
    """Raised when prices cannot be fetched from CoinGecko."""


async def fetch_prices(coin_ids: list[str], config: Config) -> dict:
    """Fetch RUB and USD prices for all requested coins in one CoinGecko request."""
    unique_coin_ids = sorted(set(coin_ids))
    if not unique_coin_ids:
        return {}

    headers = {}
    if config.coingecko_api_key:
        headers["x-cg-demo-api-key"] = config.coingecko_api_key

    params = {
        "ids": ",".join(unique_coin_ids),
        "vs_currencies": "rub,usd",
        "include_24hr_change": "true",
    }
    timeout = aiohttp.ClientTimeout(total=10)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(COINGECKO_PRICE_URL, params=params, headers=headers) as response:
                if response.status != 200:
                    body = await response.text()
                    logger.warning("CoinGecko returned %s: %s", response.status, body[:300])
                    raise CryptoAPIError("CoinGecko returned an error")
                data = await response.json()
                if not isinstance(data, dict):
                    raise CryptoAPIError("Unexpected CoinGecko response")
                return data
    except (aiohttp.ClientError, TimeoutError, CryptoAPIError) as exc:
        logger.exception("Failed to fetch prices from CoinGecko: %s", exc)
        raise CryptoAPIError from exc
