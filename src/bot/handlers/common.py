from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from bot.keyboards.admin import get_admin_menu
from utils.auth import is_admin

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    if is_admin(message):
        await message.answer("Добро пожаловать! Вы администратор. Вы можете управлять сотрудниками, используя команды в кнопках. Вы можете нанимать и уволнять сотрудников или начните смену как администратор с помощью команды /start_shift, а для закрытия смены /end_shift. Также вы можете получить id сотрудника с помощью бота @getmyid_bot.")
        await message.answer("Выберите действие:", reply_markup=get_admin_menu())
        await state.set_state("admin:choosing_action")
    else:
        await message.answer("Добро пожаловать! Зарегистрируйтесь попросив у админа или начните смену если вы зарегестрированы с помощью команды /start_shift, а для закрытия смены /end_shift.")

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.")