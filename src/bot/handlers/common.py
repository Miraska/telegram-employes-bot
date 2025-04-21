from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from bot.keyboards.admin import get_admin_menu
from utils.auth import is_admin, is_registered_employee, get_registered_employee

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    if is_admin(message) and not is_registered_employee(message):
        await message.answer("Добро пожаловать! Вы администратор. Вы можете управлять сотрудниками, используя команды в кнопках. Вы можете нанимать и уволнять сотрудников")
        await message.answer("Выберите действие:", reply_markup=get_admin_menu())
        await state.set_state("admin:choosing_action")

    elif is_registered_employee(message) and not is_admin(message):
        if get_registered_employee(message).role == "senior_manager":
            await message.answer("Добро пожаловать! Вы зарегистрированный старший сотрудник.")

        else:
            await message.answer("Добро пожаловать! Вы зарегистрированный сотрудник. Начните смену с помощью команды /start_shift, а для закрытия смены /end_shift.")

    elif is_admin(message) and is_registered_employee(message):
        if get_registered_employee(message).role == "senior_manager":
            await message.answer("Добро пожаловать! Вы администратор и зарегистрированный старший сотрудник. Вы можете управлять сотрудниками, используя команды в кнопках. Вы можете нанимать и уволнять сотрудников")
            await message.answer("Выберите действие:", reply_markup=get_admin_menu())
            await state.set_state("admin:choosing_action")
        else:
            await message.answer("Добро пожаловать! Вы администратор и зарегистрированный сотрудник. Вы можете управлять сотрудниками, используя команды в кнопках. Вы можете нанимать и уволнять сотрудников")
            await message.answer("Выберите действие:", reply_markup=get_admin_menu())
            await state.set_state("admin:choosing_action")
    
    else:
        await message.answer("Добро пожаловать! Зарегистрируйтесь попросив у админа или начните смену если вы зарегестрированы с помощью команды /start_shift, а для закрытия смены /end_shift.")

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.")