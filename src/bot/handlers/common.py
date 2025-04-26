from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.states.admin import AdminStates
from bot.keyboards.admin import get_admin_menu, get_roles_menu
from bot.keyboards.employee import get_employee_menu, get_senior_manager_menu
from utils.auth import is_admin, is_registered_employee, get_registered_employee

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
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
    await state.clear()
    await message.answer("Действие отменено.")

@router.callback_query(F.data.startswith("admin:"))
async def admin_menu_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        await callback.message.answer("Доступ запрещён.")
        await callback.answer()
        return
    action = callback.data.split(":")[1]
    if action == "Нанять сотрудника":
        await callback.message.edit_text("Выберите роль сотрудника:", reply_markup=get_roles_menu())
        await state.set_state(AdminStates.choosing_role)
    elif action == "Уволить сотрудника":
        await callback.message.edit_text("Введите Telegram ID сотрудника для увольнения:", reply_markup=None)
        await state.set_state(AdminStates.firing_id)
    await callback.answer()

@router.message(Command("menu"))
async def show_menu(message: Message):
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
        await message.answer("Ваше меню:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        await message.answer("У вас нет доступа к меню.")

@router.message(Command("my_id"))
async def get_my_id(message: Message):
    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")