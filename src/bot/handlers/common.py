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
        await message.answer("Добро пожаловать! Вы администратор. Вы можете управлять сотрудниками, используя кнопки. Вы можете нанимать и увольнять сотрудников")
        await message.answer("Выберите действие:", reply_markup=get_admin_menu())
        await state.set_state("admin:choosing_action")

    elif is_registered_employee(message) and not is_admin(message):
        if get_registered_employee(message).role == "senior_manager":
            await message.answer("Добро пожаловать! Вы зарегистрированы как старший сотрудник")

        else:
            await message.answer("Добро пожаловать! Вы зарегистрированы как сотрудник. Начните смену с помощью кнопки “Начать смену”, после открытия смены у вас будут доступны варианты работы с сменой, затем вы сможете её закрыть!")

    elif is_admin(message) and is_registered_employee(message):
        if get_registered_employee(message).role == "senior_manager":
            await message.answer("Добро пожаловать! Вы администратор и зарегистрирован, как старший сотрудник. Вы можете управлять сотрудниками, используя кнопки. Вы можете нанимать и увольнять сотрудников, а также работать с сменами")
            await message.answer("Выберите действие:", reply_markup=get_admin_menu())
            await state.set_state("admin:choosing_action")
        else:
            await message.answer("Добро пожаловать! Вы администратор и зарегистрированы, как сотрудник. Вы можете управлять сотрудниками, используя кнопки, а также работать с сменами")
            await message.answer("Выберите действие:", reply_markup=get_admin_menu())
            await state.set_state("admin:choosing_action")
    
    else:
        await message.answer("Добро пожаловать! Ваш ID не добавлен в пул сотрудников, просьба обратиться к администратору, чтобы получить необходимые права")

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.")