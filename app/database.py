from __future__ import annotations

from datetime import datetime, timezone

import aiosqlite

from app.constants import COINS_BY_ID, DEFAULT_COIN_IDS, SUPPORTED_CURRENCIES, SUPPORTED_INTERVALS


DB_PATH = "bot.db"


def configure_database(path: str) -> None:
    global DB_PATH
    DB_PATH = path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                currency TEXT DEFAULT 'rub',
                interval_minutes INTEGER DEFAULT 5,
                notifications_enabled INTEGER DEFAULT 0,
                last_sent_at TEXT NULL,
                last_manual_price_at TEXT NULL,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_coins (
                user_id INTEGER,
                coin_id TEXT,
                symbol TEXT,
                PRIMARY KEY(user_id, coin_id),
                FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS price_cache (
                coin_id TEXT,
                currency TEXT,
                price REAL,
                change_24h REAL,
                updated_at TEXT,
                PRIMARY KEY(coin_id, currency)
            )
            """
        )
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in await cursor.fetchall()}
        if "last_manual_price_at" not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN last_manual_price_at TEXT NULL")

        await db.execute(
            """
            UPDATE user_coins
            SET symbol = 'GRAM'
            WHERE coin_id = 'the-open-network'
               OR symbol = 'TON'
            """
        )
        cursor = await db.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'available_coins'"
        )
        if await cursor.fetchone():
            await db.execute(
                """
                UPDATE available_coins
                SET symbol = 'GRAM', name = 'Gram'
                WHERE coin_id = 'the-open-network'
                """
            )
        await db.commit()


async def create_user_if_not_exists(user_id: int) -> None:
    now = utc_now_iso()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        exists = await cursor.fetchone()
        if exists:
            return

        await db.execute(
            """
            INSERT INTO users (user_id, currency, interval_minutes, notifications_enabled, created_at, updated_at)
            VALUES (?, 'rub', 5, 0, ?, ?)
            """,
            (user_id, now, now),
        )
        for coin_id in DEFAULT_COIN_IDS:
            coin = COINS_BY_ID[coin_id]
            await db.execute(
                "INSERT INTO user_coins (user_id, coin_id, symbol) VALUES (?, ?, ?)",
                (user_id, coin.coin_id, coin.symbol),
            )
        await db.commit()


async def get_user_settings(user_id: int) -> dict | None:
    await create_user_if_not_exists(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_coins(user_id: int) -> list[str]:
    await create_user_if_not_exists(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT coin_id FROM user_coins WHERE user_id = ? ORDER BY rowid",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def toggle_user_coin(user_id: int, coin_id: str) -> list[str]:
    await create_user_if_not_exists(user_id)
    if coin_id not in COINS_BY_ID:
        return await get_user_coins(user_id)

    now = utc_now_iso()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM user_coins WHERE user_id = ? AND coin_id = ?",
            (user_id, coin_id),
        )
        exists = await cursor.fetchone()
        if exists:
            await db.execute(
                "DELETE FROM user_coins WHERE user_id = ? AND coin_id = ?",
                (user_id, coin_id),
            )
        else:
            coin = COINS_BY_ID[coin_id]
            await db.execute(
                "INSERT INTO user_coins (user_id, coin_id, symbol) VALUES (?, ?, ?)",
                (user_id, coin.coin_id, coin.symbol),
            )
        await db.execute("UPDATE users SET updated_at = ? WHERE user_id = ?", (now, user_id))
        await db.commit()
    return await get_user_coins(user_id)


async def set_currency(user_id: int, currency: str) -> None:
    await create_user_if_not_exists(user_id)
    if currency not in SUPPORTED_CURRENCIES:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET currency = ?, updated_at = ? WHERE user_id = ?",
            (currency, utc_now_iso(), user_id),
        )
        await db.commit()


async def set_interval(user_id: int, minutes: int) -> None:
    await create_user_if_not_exists(user_id)
    if minutes not in SUPPORTED_INTERVALS:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET interval_minutes = ?, notifications_enabled = 1, updated_at = ? WHERE user_id = ?",
            (minutes, utc_now_iso(), user_id),
        )
        await db.commit()


async def set_notifications_enabled(user_id: int, enabled: bool) -> None:
    await create_user_if_not_exists(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET notifications_enabled = ?, updated_at = ? WHERE user_id = ?",
            (1 if enabled else 0, utc_now_iso(), user_id),
        )
        await db.commit()


async def update_last_manual_price_at(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_manual_price_at = ?, updated_at = ? WHERE user_id = ?",
            (utc_now_iso(), utc_now_iso(), user_id),
        )
        await db.commit()


async def update_last_sent_at(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_sent_at = ?, updated_at = ? WHERE user_id = ?",
            (utc_now_iso(), utc_now_iso(), user_id),
        )
        await db.commit()


async def get_users_due_for_notification(now: datetime) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM users
            WHERE notifications_enabled = 1
              AND (
                last_sent_at IS NULL
                OR datetime(last_sent_at) <= datetime(?, '-' || interval_minutes || ' minutes')
              )
            """,
            (now.isoformat(),),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def upsert_price_cache(coin_id: str, currency: str, price: float, change_24h: float | None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO price_cache (coin_id, currency, price, change_24h, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(coin_id, currency) DO UPDATE SET
                price = excluded.price,
                change_24h = excluded.change_24h,
                updated_at = excluded.updated_at
            """,
            (coin_id, currency, price, change_24h, utc_now_iso()),
        )
        await db.commit()


async def upsert_prices_cache(prices: dict) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        now = utc_now_iso()
        for coin_id, values in prices.items():
            for currency in SUPPORTED_CURRENCIES:
                price = values.get(currency)
                if price is None:
                    continue
                change = values.get(f"{currency}_24h_change")
                await db.execute(
                    """
                    INSERT INTO price_cache (coin_id, currency, price, change_24h, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(coin_id, currency) DO UPDATE SET
                        price = excluded.price,
                        change_24h = excluded.change_24h,
                        updated_at = excluded.updated_at
                    """,
                    (coin_id, currency, float(price), change, now),
                )
        await db.commit()


async def get_cached_prices(coin_ids: list[str], currency: str) -> dict[str, dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        result: dict[str, dict] = {}
        for coin_id in coin_ids:
            cursor = await db.execute(
                "SELECT * FROM price_cache WHERE coin_id = ? AND currency = ?",
                (coin_id, currency),
            )
            row = await cursor.fetchone()
            if row:
                result[coin_id] = dict(row)
        return result
