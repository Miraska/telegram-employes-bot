from aiogram import Router, F
from aiogram.types import Message
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
    print("start_hire")
    if not is_admin(message):
        await message.answer("Доступ запрещён.")
        return
    await message.answer("Выберите роль:", reply_markup=get_roles_menu())
    await state.set_state(AdminStates.choosing_role)

@router.message(F.text.in_(["Обычный сотрудник", "Старший сотрудник"]))
async def choose_role(message: Message, state: FSMContext):
    role_text = message.text
    role = "manager" if role_text == "Обычный сотрудник" else "senior_manager"
    print("Роль: ", role)
    await state.update_data(role=role)
    await message.answer("Введите числовой Telegram ID (без символа @):")
    await state.set_state(AdminStates.getting_id)

@router.message(AdminStates.getting_id)
async def get_id(message: Message, state: FSMContext):
    employee_input = message.text.strip()
    if employee_input.startswith('@'):
        username = employee_input[1:]
        await state.update_data(telegram_id=username, username=username)
    else:
        if not employee_input.isdigit():
            await message.answer("Telegram ID должен состоять только из цифр или начинаться с '@'. Попробуйте еще раз.")
            return
        await state.update_data(telegram_id=employee_input, username=None)
    await message.answer("Введите ФИО сотрудника:")
    await state.set_state(AdminStates.getting_fio)


@router.message(AdminStates.getting_fio)
async def get_fio(message: Message, state: FSMContext):
    full_name = message.text.strip()
    if full_name.startswith('/'):
        await message.answer("Пожалуйста, введите корректное ФИО сотрудника, а не команду.")
        return
    data = await state.get_data()
    with SessionLocal() as db:
        employee = create_employee(
            db=db,
            telegram_id=data.get("telegram_id"),
            username=data.get("username"),  # Здесь будет None
            full_name=full_name,
            role=data["role"],
            trading_point="Патриарши"  # Значение по умолчанию для примера
        )
        airtable_data = {
            "telegram_id": employee.telegram_id,
            "username": employee.username,
            "full_name": employee.full_name,
            "role": employee.role,
            "hired_at": employee.hired_at.isoformat()
        }
        send_to_airtable("hire", airtable_data)
    await message.answer(f"Сотрудник {employee.full_name} нанят как {employee.role}!")
    await state.clear()

@router.message(F.text == "Уволить сотрудника")
async def start_fire(message: Message, state: FSMContext):
    if not is_admin(message):
        await message.answer("Доступ запрещён.")
        return
    await message.answer("Введите Telegram ID (без @) для увольнения:")
    await state.set_state(AdminStates.firing_id)

@router.message(AdminStates.firing_id)
async def fire_employee_handler(message: Message, state: FSMContext):
    with SessionLocal() as db:
        employee = fire_employee(db, message.text.strip())
        if employee:
            airtable_data = {
                "telegram_id": employee.telegram_id,
                "username": employee.username,
                "full_name": employee.full_name,
                "fired_at": employee.fired_at.isoformat()
            }
            send_to_airtable("fire", airtable_data)
            await message.answer(f"Сотрудник {employee.full_name} уволен.")
        else:
            await message.answer("Сотрудник не найден.")
    await state.clear()
