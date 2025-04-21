import asyncio
import logging
from aiogram import Bot, Dispatcher
from config.settings import settings_config
from database.models import init_db
from bot.handlers import common, admin, employee
from utils.logging import setup_logging


setup_logging()
logger = logging.getLogger(__name__)

async def main():
    init_db()
    bot = Bot(token=settings_config.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()

    print(settings_config.BOT_TOKEN)
    print(settings_config.ADMIN_USERNAMES)

    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(employee.router)

    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot session closed.")

if __name__ == "__main__":
    asyncio.run(main())