from aiogram import Router, F, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from bot.keyboards.admin import get_admin_menu, get_roles_menu
from bot.keyboards.employee import get_employee_menu, get_senior_manager_menu
from utils.auth import is_admin, is_registered_employee, get_registered_employee

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    if is_admin(message) and not is_registered_employee(message):
        await message.answer("Добро пожаловать! Вы администратор. Вы можете управлять сотрудниками, используя кнопки.")
        await message.answer("Выберите действие:", reply_markup=get_admin_menu())
        await state.set_state("admin:choosing_action")
    elif is_registered_employee(message) and not is_admin(message):
        if get_registered_employee(message).role == "senior_manager":
            await message.answer("Добро пожаловать! Вы зарегистрированы как старший сотрудник")
        else:
            await message.answer("Добро пожаловать! Вы зарегистрированы как сотрудник. Начните смену с помощью команды /start_shift")
    elif is_admin(message) and is_registered_employee(message):
        employee = get_registered_employee(message)
        if employee.role == "senior_manager":
            await message.answer("Добро пожаловать! Вы администратор и зарегистрированы как старший сотрудник.")
        else:
            await message.answer("Добро пожаловать! Вы администратор и зарегистрированы как сотрудник.")
        await message.answer("Выберите действие:", reply_markup=get_combined_menu(employee.role))
        await state.set_state("admin:choosing_action")
    else:
        await message.answer("Добро пожаловать! Ваш ID не добавлен в пул сотрудников, обратитесь к администратору.")

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.")

@router.callback_query(F.data.startswith("admin:"))
async def admin_menu_handler(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data.split(":")[1]
    if action == "Нанять сотрудника":
        await callback_query.message.edit_text("Выберите роль сотрудника:", reply_markup=get_roles_menu())
        await state.set_state("admin:choosing_role")
    elif action == "Уволить сотрудника":
        await callback_query.message.edit_text("Введите Telegram ID сотрудника для увольнения:")
        await state.set_state("admin:firing_id")
    await callback_query.answer()

@router.message(Command("menu"))
async def show_menu(message: Message):
    if is_admin(message):
        if is_registered_employee(message):
            employee = get_registered_employee(message)
            await message.answer("Ваше меню:", reply_markup=get_combined_menu(employee.role))
        else:
            await message.answer("Админ-меню:", reply_markup=get_admin_menu())
    elif is_registered_employee(message):
        employee = get_registered_employee(message)
        if employee.role == "senior_manager":
            await message.answer("Меню старшего сотрудника:", reply_markup=get_senior_manager_menu())
        else:
            await message.answer("Меню сотрудника:", reply_markup=get_employee_menu())
    else:
        await message.answer("У вас нет доступа к меню.")

def get_combined_menu(role):
    admin_buttons = [
        InlineKeyboardButton(text="Нанять сотрудника", callback_data="admin:Нанять сотрудника"),
        InlineKeyboardButton(text="Уволить сотрудника", callback_data="admin:Уволить сотрудника")
    ]
    if role == "senior_manager":
        employee_buttons = [InlineKeyboardButton(text="Выполнить проверку", callback_data="action:perform_check")]
    else:
        employee_buttons = [
            InlineKeyboardButton(text="Начать смену", callback_data="action:start_shift"),
            InlineKeyboardButton(text="Завершить смену", callback_data="action:end_shift")
        ]
    return InlineKeyboardMarkup(inline_keyboard=[admin_buttons, employee_buttons])


@router.message(Command("my_id"))
async def get_my_id(message: Message):
    user_id = message.from_user.id
    await message.answer(f"Ваш Telegram ID: {user_id}")