from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from bot.states.employee import EmployeeStates
from bot.keyboards.employee import get_shift_buttons, get_trading_points
from database.crud import get_employee_by_id, create_shift, end_shift
from database.models import SessionLocal, Shift
from services.airtable import send_to_airtable, upload_to_yandex_cloud
from utils.auth import is_admin, is_registered_employee
from datetime import datetime
from PIL import Image
import os

router = Router()

def compress_image(input_path: str, output_path: str, max_size=(800, 800), quality=70):
    with Image.open(input_path) as img:
        img.thumbnail(max_size, Image.ANTIALIAS)
        img.save(output_path, format="JPEG", quality=quality)


@router.message(Command("start_shift"))
async def start_shift(message: Message, state: FSMContext):
    if not is_registered_employee(message):
        await message.answer("Вы не зарегистрированы. Обратитесь к администратору.")
        return
    await message.answer("Выберите торговую точку:", reply_markup=get_trading_points())
    await state.set_state(EmployeeStates.waiting_for_trading_point)

@router.message(F.text.in_(["Патриарши", "Торговая точка 1", "Торговая точка 2"]))
async def process_trading_point(message: Message, state: FSMContext):
    trading_point = message.text
    await state.update_data(trading_point=trading_point)
    await message.answer("Введите сумму наличных на начало дня:")
    await state.set_state(EmployeeStates.waiting_for_cash_start)

@router.message(EmployeeStates.waiting_for_cash_start)
async def process_cash_start(message: Message, state: FSMContext):
    try:
        cash_start = int(message.text)
        await state.update_data(cash_start=cash_start)
        await message.answer("Отправьте фото начала смены:")
        await state.set_state(EmployeeStates.waiting_for_photo_start)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_photo_start, F.photo)
async def process_photo_start(message: Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    temp_path = f"temp_{message.from_user.id}.jpg"
    compressed_path = f"compressed_{message.from_user.id}.jpg"
    await bot.download_file(file_path=file.file_path, destination=temp_path)

    compress_image(temp_path, compressed_path)
    os.remove(temp_path)

    data = await state.get_data()
    with SessionLocal() as db:
        employee = get_employee_by_id(db, str(message.from_user.id))
        if employee is None:
            await message.answer("Сотрудник не найден. Вы не зарегистрированы для работы со сменами.")
            os.remove(compressed_path)
            await state.clear()
            return
        
        photo_url = upload_to_yandex_cloud(compressed_path)
        
        shift = create_shift(db, employee.id, data["trading_point"], data["cash_start"], photo_url)
        airtable_data = {
            "employee_id": employee.telegram_id,
            "trading_point": shift.trading_point,
            "cash_start": shift.cash_start,
            "start_time": shift.start_time.isoformat(),
            "photo_url": photo_url  # Добавляем URL в данные для Airtable
        }
        send_to_airtable("shift_start", airtable_data, compressed_path)
    os.remove(compressed_path)
    await message.answer("Смена начата! Используйте кнопки для перерывов.", reply_markup=get_shift_buttons())
    await state.update_data(shift_id=shift.id)
    await state.set_state(None)

@router.message(Command("end_shift"))
async def end_shift_cmd(message: Message, state: FSMContext):
    if not is_registered_employee(message):
        await message.answer("Вы не зарегистрированы.")
        return
    with SessionLocal() as db:
        employee = get_employee_by_id(db, str(message.from_user.id))
        shift = db.query(Shift).filter(Shift.employee_id == employee.id, Shift.end_time == None).first()
        if not shift:
            await message.answer("Активная смена не найдена.")
            return
    await state.update_data(shift_id=shift.id)
    await message.answer("Введите приход наличных:")
    await state.set_state(EmployeeStates.waiting_for_cash_income)

@router.message(EmployeeStates.waiting_for_cash_income)
async def process_cash_income(message: Message, state: FSMContext):
    try:
        cash_income = int(message.text)
        await state.update_data(cash_income=cash_income)
        await message.answer("Введите приход безналичных:")
        await state.set_state(EmployeeStates.waiting_for_cashless_income)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_cashless_income)
async def process_cashless_income(message: Message, state: FSMContext):
    try:
        cashless_income = int(message.text)
        await state.update_data(cashless_income=cashless_income)
        await message.answer("Введите итог:")
        await state.set_state(EmployeeStates.waiting_for_total)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_total)
async def process_total(message: Message, state: FSMContext):
    try:
        total = int(message.text)
        await state.update_data(total=total)
        await message.answer("Введите расходы (или '-'):")
        await state.set_state(EmployeeStates.waiting_for_expenses)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_expenses)
async def process_expenses(message: Message, state: FSMContext):
    expenses = message.text
    await state.update_data(expenses=expenses)
    await message.answer("Введите остаток наличных:")
    await state.set_state(EmployeeStates.waiting_for_balance)

@router.message(EmployeeStates.waiting_for_balance)
async def process_balance(message: Message, state: FSMContext):
    try:
        balance = int(message.text)
        await state.update_data(balance=balance)
        await message.answer("Отправьте фото окончания смены:")
        await state.set_state(EmployeeStates.waiting_for_photo_end)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_photo_end, F.photo)
async def process_photo_end(message: Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    temp_path = f"temp_{message.from_user.id}_end.jpg"
    compressed_path = f"compressed_{message.from_user.id}_end.jpg"
    await bot.download_file(file_path=file.file_path, destination=temp_path)

    compress_image(temp_path, compressed_path)
    os.remove(temp_path)

    data = await state.get_data()
    with SessionLocal() as db:
        photo_url = upload_to_yandex_cloud(compressed_path)
        
        shift = end_shift(
            db, data["shift_id"], data["cash_income"], data["cashless_income"],
            data["total"], data["expenses"], data["balance"], photo_url
        )
        airtable_data = {
            "employee_id": str(message.from_user.id),
            "trading_point": shift.trading_point,
            "cash_income": shift.cash_income,
            "cashless_income": shift.cashless_income,
            "total": shift.total,
            "expenses": shift.expenses,
            "balance": shift.balance,
            "end_time": shift.end_time.isoformat(),
            "photo_url": photo_url  # Добавляем URL в данные для Airtable
        }
        send_to_airtable("shift_end", airtable_data, compressed_path)
    os.remove(compressed_path)
    await message.answer("Смена завершена!")
    await state.clear()

@router.message(F.text.in_(["Отошел", "отошел"]))
async def break_start(message: Message):
    with SessionLocal() as db:
        employee = get_employee_by_id(db, str(message.from_user.id))
        if not employee:
            await message.answer("Вы не зарегистрированы.")
            return
        shift = db.query(Shift).filter(Shift.employee_id == employee.id, Shift.end_time == None).first()
        if not shift:
            await message.answer("Смена не начата.")
            return
        if shift.break_start_at:
            await message.answer("Вы уже на перерыве.")
            return
        shift.break_start_at = datetime.utcnow()
        db.commit()
        await message.answer("Перерыв начат.")

@router.message(F.text.in_(["Пришел", "пришел"]))
async def break_end(message: Message):
    with SessionLocal() as db:
        employee = get_employee_by_id(db, str(message.from_user.id))
        if not employee:
            await message.answer("Вы не зарегистрированы.")
            return
        shift = db.query(Shift).filter(Shift.employee_id == employee.id, Shift.end_time == None).first()
        if not shift or not shift.break_start_at:
            await message.answer("Перерыв не начат.")
            return
        break_duration = int((datetime.utcnow() - shift.break_start_at).total_seconds() / 60)
        shift.total_break_minutes += break_duration
        shift.break_start_at = None
        db.commit()
        airtable_data = {
            "employee_id": employee.telegram_id,
            "break_duration_minutes": break_duration,
            "total_break_minutes": shift.total_break_minutes
        }
        send_to_airtable("break", airtable_data)
        await message.answer(f"Перерыв окончен. Длительность: {break_duration} мин.")
