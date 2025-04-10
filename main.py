import asyncio
import logging
from aiogram import F, Bot, Dispatcher

from config.settings import settings
from handlers import common, hire, fire
from database.models import init_db
from states.hire_fire import HireFireStates
from aiogram.filters import CommandStart

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    init_db()
    
    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    
    dp.message.register(common.cmd_start, CommandStart())
    
    dp.message.register(
        hire.choose_action_hire, 
        HireFireStates.choosing_action, 
        F.text.casefold() == "нанять сотрудника"
    )
    dp.message.register(
        fire.choose_action_fire, 
        HireFireStates.choosing_action, 
        F.text.casefold() == "уволить сотрудника"
    )
    
    dp.message.register(hire.choose_role, HireFireStates.choosing_role, F.text)
    dp.message.register(hire.get_tg_id, HireFireStates.get_tg_id, F.text)
    dp.message.register(hire.get_fio, HireFireStates.get_fio, F.text)
    
    dp.message.register(fire.get_fire_id, HireFireStates.get_fire_id, F.text)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка в боте: {e}", exc_info=True)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем.")
    except Exception as e:
        logger.error(f"Ошибка в основном цикле: {e}", exc_info=True)
        raise
    finally:
        logger.info("Завершение работы бота.")