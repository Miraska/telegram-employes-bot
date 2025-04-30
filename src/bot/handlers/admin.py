from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.states.admin import AdminStates
from bot.keyboards.admin import get_roles_menu
from database.crud import create_employee, fire_employee
from database.models import SessionLocal
from services.airtable import send_to_airtable
from utils.auth import is_admin
from .common import get_main_menu

router = Router()

# Определяем состояния для процесса найма
class HireEmployeeStates(StatesGroup):
    choosing_role = State()       # Выбор роли
    getting_id = State()          # Ввод Telegram ID
    getting_fio = State()         # Ввод ФИО
    confirming = State()          # Подтверждение данных
    editing = State()             # Редактирование данных

# Функция для создания клавиатуры подтверждения
def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data="confirm:yes")],
        [InlineKeyboardButton(text="Редактировать", callback_data="confirm:edit")],
        [InlineKeyboardButton(text="Отмена", callback_data="confirm:cancel")]
    ])

# Функция для создания клавиатуры редактирования
def get_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Роль", callback_data="edit:role")],
        [InlineKeyboardButton(text="Telegram ID", callback_data="edit:telegram_id")],
        [InlineKeyboardButton(text="ФИО", callback_data="edit:full_name")],
        [InlineKeyboardButton(text="Назад к подтверждению", callback_data="edit:back")]
    ])

# Обработка меню администратора
@router.callback_query(F.data.startswith("admin:"))
async def admin_menu_handler(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        await callback.message.answer("Доступ запрещён.")
        await callback.answer()
        return
    action = callback.data.split(":")[1]
    
    if action == "hire_employee":
        await callback.message.edit_text("Выберите роль сотрудника:", reply_markup=get_roles_menu())
        await state.set_state(HireEmployeeStates.choosing_role)
    elif action == "fire_employee":
        await callback.message.edit_text("Введите Telegram ID сотрудника для увольнения:")
        await state.set_state(AdminStates.firing_id)
    await callback.answer()

# Начало процесса найма
@router.message(F.text == "Нанять сотрудника")
async def start_hire(message: Message, state: FSMContext):
    if not is_admin(message):
        return await message.answer("Доступ запрещён.")
    await message.answer("Выберите роль сотрудника:", reply_markup=get_roles_menu())
    await state.set_state(HireEmployeeStates.choosing_role)

# Обработка выбора роли
@router.callback_query(F.data.startswith("role:"), HireEmployeeStates.choosing_role)
async def process_role(callback: CallbackQuery, state: FSMContext):
    role_text = callback.data.split(":", 1)[1]
    role = "manager" if role_text == "Обычный сотрудник" else "senior_manager"
    await state.update_data(role=role)
    data = await state.get_data()
    # Если все данные уже есть (при редактировании), возвращаемся к подтверждению
    if "telegram_id" in data and "full_name" in data:
        await show_confirmation(callback, state)
    else:
        await callback.message.edit_text("Введите числовой Telegram ID сотрудника:")
        await state.set_state(HireEmployeeStates.getting_id)
    await callback.answer()

# Обработка ввода Telegram ID
@router.message(HireEmployeeStates.getting_id)
async def process_id(message: Message, state: FSMContext):
    telegram_id = message.text.strip()
    if not telegram_id.isdigit():
        return await message.answer("Пожалуйста, введите числовой Telegram ID.")
    await state.update_data(telegram_id=telegram_id)
    data = await state.get_data()
    # Если все данные уже есть (при редактировании), возвращаемся к подтверждению
    if "role" in data and "full_name" in data:
        await show_confirmation_message(message, state)
    else:
        await message.answer("Введите ФИО сотрудника:")
        await state.set_state(HireEmployeeStates.getting_fio)

# Обработка ввода ФИО
@router.message(HireEmployeeStates.getting_fio)
async def process_fio(message: Message, state: FSMContext):
    full_name = message.text.strip()
    if full_name.startswith("/"):
        return await message.answer("Введите корректное ФИО, а не команду.")
    await state.update_data(full_name=full_name)
    await show_confirmation_message(message, state)

# Функция для отображения подтверждения (для сообщений)
async def show_confirmation_message(message: Message, state: FSMContext):
    data = await state.get_data()
    role_display = "Обычный сотрудник" if data['role'] == "manager" else "Старший сотрудник"
    confirmation_text = (
        "Проверьте данные:\n"
        f"Роль: {role_display}\n"
        f"Telegram ID: {data['telegram_id']}\n"
        f"ФИО: {data['full_name']}\n\n"
        "Все верно?"
    )
    await message.answer(confirmation_text, reply_markup=get_confirmation_keyboard())
    await state.set_state(HireEmployeeStates.confirming)

# Функция для отображения подтверждения (для callback)
async def show_confirmation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    role_display = "Обычный сотрудник" if data['role'] == "manager" else "Старший сотрудник"
    confirmation_text = (
        "Проверьте данные:\n"
        f"Роль: {role_display}\n"
        f"Telegram ID: {data['telegram_id']}\n"
        f"ФИО: {data['full_name']}\n\n"
        "Все верно?"
    )
    await callback.message.edit_text(confirmation_text, reply_markup=get_confirmation_keyboard())
    await state.set_state(HireEmployeeStates.confirming)

# Обработка подтверждения или редактирования
@router.callback_query(F.data.startswith("confirm:"), HireEmployeeStates.confirming)
async def process_confirmation(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":", 1)[1]
    data = await state.get_data()
    
    if action == "yes":
        # Сохранение данных
        with SessionLocal() as db:
            old = fire_employee(db, data["telegram_id"])
            if old:
                send_to_airtable("fire", {
                    "telegram_id": old.telegram_id,
                    "username": old.username,
                    "full_name": old.full_name,
                    "fired_at": old.fired_at and old.fired_at.isoformat()
                })
            emp = create_employee(
                db,
                telegram_id=data["telegram_id"],
                username=None,
                full_name=data["full_name"],
                role=data["role"],
                trading_point="Патриарши"
            )
            send_to_airtable("hire", {
                "telegram_id": emp.telegram_id,
                "username": emp.username,
                "full_name": emp.full_name,
                "role": emp.role,
                "hired_at": emp.hired_at and emp.hired_at.isoformat()
            })
        await callback.message.edit_text(f"Сотрудник {emp.full_name} нанят как {emp.role}!", reply_markup=get_main_menu(callback.message))
        await state.clear()
    
    elif action == "edit":
        # Переход к редактированию
        await state.set_state(HireEmployeeStates.editing)
        role_display = "Обычный сотрудник" if data['role'] == "manager" else "Старший сотрудник"
        edit_text = (
            "Выберите, что хотите отредактировать:\n"
            f"Роль: {role_display}\n"
            f"Telegram ID: {data['telegram_id']}\n"
            f"ФИО: {data['full_name']}"
        )
        await callback.message.edit_text(edit_text, reply_markup=get_edit_keyboard())
    
    elif action == "cancel":
        # Отмена
        await callback.message.edit_text("Процесс найма отменен.", reply_markup=get_main_menu(callback.message))
        await state.clear()
    
    await callback.answer()

# Обработка редактирования
@router.callback_query(F.data.startswith("edit:"), HireEmployeeStates.editing)
async def process_edit(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":", 1)[1]
    
    if field == "role":
        await callback.message.edit_text("Выберите новую роль сотрудника:", reply_markup=get_roles_menu())
        await state.set_state(HireEmployeeStates.choosing_role)
    elif field == "telegram_id":
        await callback.message.edit_text("Введите новый числовой Telegram ID сотрудника:")
        await state.set_state(HireEmployeeStates.getting_id)
    elif field == "full_name":
        await callback.message.edit_text("Введите новое ФИО сотрудника:")
        await state.set_state(HireEmployeeStates.getting_fio)
    elif field == "back":
        # Возврат к подтверждению
        await show_confirmation(callback, state)
    
    await callback.answer()

# Процесс увольнения
@router.message(F.text == "Уволить сотрудника")
async def start_fire(message: Message, state: FSMContext):
    if not is_admin(message):
        return await message.answer("Доступ запрещён.")
    await message.answer("Введите числовой Telegram ID сотрудника:")
    await state.set_state(AdminStates.firing_id)

@router.message(AdminStates.firing_id)
async def fire_employee_handler(message: Message, state: FSMContext):
    tid = message.text.strip()
    if not tid.isdigit():
        return await message.answer("Пожалуйста, введите числовой Telegram ID.")
    with SessionLocal() as db:
        emp = fire_employee(db, tid)
        if emp:
            send_to_airtable("fire", {
                "telegram_id": emp.telegram_id,
                "username": emp.username,
                "full_name": emp.full_name,
                "fired_at": emp.fired_at and emp.fired_at.isoformat()
            })
            await message.answer(f"Сотрудник {emp.full_name} уволен.", reply_markup=get_main_menu(message))
        else:
            await message.answer("Сотрудник не найден.", reply_markup=get_main_menu(message))
    await state.clear()