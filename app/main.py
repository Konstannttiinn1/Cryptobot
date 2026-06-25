from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties

from app.config import get_config
from app.database import configure_database, init_db
from app.handlers import setup_router
from app.scheduler import scheduler_loop


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config = get_config()
    configure_database(config.database_path)
    await init_db()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Главное меню"),
            BotCommand(command="menu", description="Открыть меню"),
            BotCommand(command="price", description="Курс сейчас"),
            BotCommand(command="coins", description="Выбрать монеты"),
            BotCommand(command="settings", description="Настройки"),
            BotCommand(command="stop", description="Отключить уведомления"),
            BotCommand(command="hide", description="Скрыть клавиатуру"),
        ]
    )

    dispatcher = Dispatcher()
    dispatcher.include_router(setup_router(config))

    stop_event = asyncio.Event()
    scheduler_task = asyncio.create_task(scheduler_loop(bot, config, stop_event))

    try:
        await dispatcher.start_polling(bot)
    finally:
        stop_event.set()
        scheduler_task.cancel()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
