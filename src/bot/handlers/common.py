from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.states.admin import AdminStates
from bot.keyboards.admin import get_admin_menu, get_roles_menu
from bot.keyboards.employee import get_employee_menu, get_senior_manager_menu
from utils.auth import is_admin, is_registered_employee, get_registered_employee

router = Router()

# Функция для добавления кнопки "Назад"
def add_back_button_common(keyboard: InlineKeyboardMarkup = None) -> InlineKeyboardMarkup:
    back_button = InlineKeyboardButton(text="Назад", callback_data="common:back")
    if keyboard is None:
        return InlineKeyboardMarkup(inline_keyboard=[[back_button]])
    else:
        keyboard.inline_keyboard.append([back_button])
        return keyboard

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Обработать команду /start и показать главное меню."""
    await state.clear()
    keyboard = []

    if is_admin(message):
        keyboard.append([InlineKeyboardButton(text="Нанять сотрудника", callback_data="admin:Нанять сотрудника")])
        keyboard.append([InlineKeyboardButton(text="Уволить сотрудника", callback_data="admin:Уволить сотрудника")])

    if is_registered_employee(message.from_user.id):
        emp = get_registered_employee(message.from_user.id)
        if emp.role == "manager":
            keyboard.append([InlineKeyboardButton(text="Начать смену", callback_data="action:start_shift")])
            keyboard.append([InlineKeyboardButton(text="Завершить смену", callback_data="action:end_shift")])
        elif emp.role == "senior_manager":
            keyboard.append([InlineKeyboardButton(text="Выполнить проверку", callback_data="action:perform_check")])

    if keyboard:
        await message.answer("Добро пожаловать! Выберите действие:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        await message.answer("Добро пожаловать! Ваш ID не добавлен в пул сотрудников, обратитесь к администратору.")

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    """Отменить текущее действие."""
    await state.clear()
    await message.answer("Действие отменено.")

@router.callback_query(F.data.startswith("admin:"))
async def admin_menu_handler(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор действия в админском меню."""
    if not is_admin(callback):
        await callback.message.answer("Доступ запрещён.")
        await callback.answer()
        return
    action = callback.data.split(":")[1]
    if action == "Нанять сотрудника":
        await callback.message.edit_text("Выберите роль сотрудника:", reply_markup=add_back_button_common(get_roles_menu()))
        await state.set_state(AdminStates.choosing_role)
    elif action == "Уволить сотрудника":
        await callback.message.edit_text("Введите Telegram ID сотрудника для увольнения:", reply_markup=add_back_button_common())
        await state.set_state(AdminStates.firing_id)
    await callback.answer()

@router.message(Command("menu"))
async def show_menu(message: Message):
    """Показать меню пользователя с помощью команды /menu."""
    keyboard = []

    if is_admin(message):
        keyboard.append([InlineKeyboardButton(text="Нанять сотрудника", callback_data="admin:Нанять сотрудника")])
        keyboard.append([InlineKeyboardButton(text="Уволить сотрудника", callback_data="admin:Уволить сотрудника")])

    if is_registered_employee(message.from_user.id):
        emp = get_registered_employee(message.from_user.id)
        if emp.role == "manager":
            keyboard.append([InlineKeyboardButton(text="Начать смену", callback_data="action:start_shift")])
            keyboard.append([InlineKeyboardButton(text="Завершить смену", callback_data="action:end_shift")])
        elif emp.role == "senior_manager":
            keyboard.append([InlineKeyboardButton(text="Выполнить проверку", callback_data="action:perform_check")])

    if keyboard:
        await message.answer("Ваше меню:", reply_markup=add_back_button_common(InlineKeyboardMarkup(inline_keyboard=keyboard)))
    else:
        await message.answer("У вас нет доступа к меню.")

@router.message(Command("my_id"))
async def get_my_id(message: Message):
    """Показать Telegram ID пользователя."""
    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")

@router.callback_query(F.data == "common:back")
async def common_back_handler(callback: CallbackQuery, state: FSMContext):
    """Обработать нажатие кнопки 'Назад' в общем меню."""
    await state.clear()
    keyboard = []

    if is_admin(callback):
        keyboard.append([InlineKeyboardButton(text="Нанять сотрудника", callback_data="admin:Нанять сотрудника")])
        keyboard.append([InlineKeyboardButton(text="Уволить сотрудника", callback_data="admin:Уволить сотрудника")])

    if is_registered_employee(callback.from_user.id):
        emp = get_registered_employee(callback.from_user.id)
        if emp.role == "manager":
            keyboard.append([InlineKeyboardButton(text="Начать смену", callback_data="action:start_shift")])
            keyboard.append([InlineKeyboardButton(text="Завершить смену", callback_data="action:end_shift")])
        elif emp.role == "senior_manager":
            keyboard.append([InlineKeyboardButton(text="Выполнить проверку", callback_data="action:perform_check")])

    if keyboard:
        await callback.message.edit_text("Добро пожаловать! Выберите действие:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        await callback.message.edit_text("Добро пожаловать! Ваш ID не добавлен в пул сотрудников, обратитесь к администратору.")
    await callback.answer()