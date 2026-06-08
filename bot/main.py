import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN, DATABASE_URL
from bot.handlers import start, accounts, products, orders, analytics, finances, errors
from bot.middlewares import DbSessionMiddleware
from db.engine import init_db, close_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Initializing database...")
    await init_db(DATABASE_URL)

    logger.info("Starting bot...")
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    dp.include_router(start.router)
    dp.include_router(accounts.router)
    dp.include_router(products.router)
    dp.include_router(orders.router)
    dp.include_router(analytics.router)
    dp.include_router(finances.router)
    dp.include_router(errors.router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await close_db()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
