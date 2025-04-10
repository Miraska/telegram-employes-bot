from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from states.hire_fire import HireFireStates
from keyboards.main import get_roles_kb
from database.crud import create_employee
from database.models import SessionLocal
from services.airtable import send_to_airtable
from aiogram.types import ReplyKeyboardRemove

async def choose_action_hire(message: Message, state: FSMContext):
    await message.answer(
        "Выберите уровень полномочий:",
        reply_markup=get_roles_kb()
    )
    await state.set_state(HireFireStates.choosing_role)

async def choose_role(message: Message, state: FSMContext):
    if message.text not in ["Обычный менеджер", "Старший менеджер", "Администратор"]:
        await message.answer("Пожалуйста, выберите роль из предложенных вариантов.")
        return
    
    await state.update_data(role=message.text)
    await message.answer(
        "Укажите ID или Telegram @username сотрудника:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(HireFireStates.get_tg_id)

async def get_tg_id(message: Message, state: FSMContext):
    employee_id = message.text.strip()
    if employee_id.startswith('@'):
        username = employee_id[1:]
        telegram_id = None
    else:
        username = None
        telegram_id = employee_id
    
    await state.update_data({
        "employee_id": employee_id,
        "username": username,
        "telegram_id": telegram_id
    })
    
    await message.answer("Введите ФИО сотрудника:")
    await state.set_state(HireFireStates.get_fio)

async def get_fio(message: Message, state: FSMContext):
    fio = message.text.strip()
    data = await state.get_data()
    
    with SessionLocal() as db:
        employee = create_employee(
            db=db,
            telegram_id=data.get("telegram_id"),
            username=data.get("username"),
            full_name=fio,
            role=data.get("role")
        )
        
        # Отправляем данные в Airtable
        airtable_data = {
            "role": employee.role,
            "employee_id": employee.telegram_id or f"@{employee.username}",
            "fio": employee.full_name,
            "hired_at": employee.hired_at.isoformat()
        }
        send_to_airtable("hire", airtable_data)
        
        await message.answer(
            f"Сотрудник {employee.full_name} принят на должность {employee.role}!\n"
            f"ID: {employee.telegram_id or f'@{employee.username}'}"
        )
    
    await state.clear()