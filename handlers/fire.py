from aiogram import F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.hire_fire import HireFireStates
from database.crud import get_employee_by_id, fire_employee
from database.models import SessionLocal
from services.airtable import send_to_airtable
from aiogram.types import ReplyKeyboardRemove

async def choose_action_fire(message: Message, state: FSMContext):
    await message.answer(
        "Укажите ID или Telegram @username сотрудника, которого нужно уволить:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(HireFireStates.get_fire_id)

async def get_fire_id(message: Message, state: FSMContext):
    employee_id = message.text.strip()
    
    with SessionLocal() as db:
        employee = fire_employee(db, employee_id)
        if not employee:
            await message.answer("Сотрудник не найден!")
            await state.clear()
            return
        
        # Отправляем данные в Airtable
        airtable_data = {
            "employee_id": employee.telegram_id or f"@{employee.username}",
            "fio": employee.full_name,
            "role": employee.role,
            "fired_at": employee.fired_at.isoformat()
        }
        send_to_airtable("fire", airtable_data)
        
        await message.answer(
            f"Сотрудник {employee.full_name} уволен.\n"
            f"Должность: {employee.role}\n"
            f"Дата увольнения: {employee.fired_at.strftime('%d.%m.%Y %H:%M')}"
        )
    
    await state.clear()