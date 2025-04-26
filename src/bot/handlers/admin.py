from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states.admin import AdminStates
from bot.keyboards.admin import get_admin_menu, get_roles_menu
from database.crud import create_employee, fire_employee
from database.models import SessionLocal
from services.airtable import send_to_airtable
from utils.auth import is_admin

router = Router()

@router.message(F.text == "Нанять сотрудника")
async def start_hire(message: Message, state: FSMContext):
    if not is_admin(message):
        return await message.answer("Доступ запрещён.")
    await message.answer("Выберите роль сотрудника:", reply_markup=get_roles_menu())
    await state.set_state(AdminStates.choosing_role)

@router.callback_query(F.data.startswith("role:"), AdminStates.choosing_role)
async def choose_role(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback):
        await callback.message.answer("Доступ запрещён.")
        await callback.answer()
        return
    role_text = callback.data.split(":", 1)[1]
    role = "manager" if role_text == "Обычный сотрудник" else "senior_manager"
    await state.update_data(role=role)
    await callback.message.edit_text("Введите числовой Telegram ID сотрудника:", reply_markup=None)
    await state.set_state(AdminStates.getting_id)
    await callback.answer()

@router.message(AdminStates.getting_id)
async def get_id(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("Пожалуйста, введите числовой Telegram ID.")
    await state.update_data(telegram_id=text, username=None)
    await message.answer("Введите ФИО сотрудника:")
    await state.set_state(AdminStates.getting_fio)

@router.message(AdminStates.getting_fio)
async def get_fio(message: Message, state: FSMContext):
    full_name = message.text.strip()
    if full_name.startswith("/"):
        return await message.answer("Введите корректное ФИО, а не команду.")
    data = await state.get_data()
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
            username=data.get("username"),
            full_name=full_name,
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
    await message.answer(f"Сотрудник {emp.full_name} нанят как {emp.role}!")
    await state.clear()

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
            await message.answer(f"Сотрудник {emp.full_name} уволен.")
        else:
            await message.answer("Сотрудник не найден.")
    await state.clear()