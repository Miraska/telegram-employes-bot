from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from bot.states.employee import EmployeeStates
from bot.keyboards.employee import get_shift_buttons, get_trading_points, yes_no_keyboard, get_cleaning_buttons, layout_keyboard, opening_time_keyboard, waste_time_keyboard
from database.crud import create_check, get_employee_by_id, create_shift, end_shift
from database.models import SessionLocal, Shift
from services.airtable import send_to_airtable, upload_to_yandex_cloud
from utils.auth import is_admin, is_registered_employee, get_registered_employee
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
    await state.set_state(None)
    await state.clear()

    if not is_registered_employee(message):
        await message.answer("Вы не зарегистрированы. Обратитесь к администратору.")
        return
    elif get_registered_employee(message).role == "senior_manager":
        await message.answer("Вы не можете начать смену, так как вы являетесь старшим сотрудником.")
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
        # Переходим к блоку дополнительных вопросов
        await message.answer("Подсветка включена? (Да/Нет)", reply_markup=yes_no_keyboard())
        await state.set_state(EmployeeStates.waiting_for_light_on)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_light_on, F.text.in_(["Да", "Нет"]))
async def process_light_on(message: Message, state: FSMContext):
    is_light_on = (message.text == "Да")
    await state.update_data(is_light_on=is_light_on)
    await message.answer("Камера подключена? (Да/Нет)", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_camera_on)

@router.message(EmployeeStates.waiting_for_camera_on, F.text.in_(["Да", "Нет"]))
async def process_camera_on(message: Message, state: FSMContext):
    is_camera_on = (message.text == "Да")
    await state.update_data(is_camera_on=is_camera_on)
    await message.answer("Выкладка в норме? (Да/Нет)", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_display_ok)

@router.message(EmployeeStates.waiting_for_display_ok, F.text.in_(["Да", "Нет"]))
async def process_display_ok(message: Message, state: FSMContext):
    is_display_ok = (message.text == "Да")
    await state.update_data(is_display_ok=is_display_ok)
    await message.answer("Влажная уборка не требуется? (Да/Нет)", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_wet_cleaning)

@router.message(EmployeeStates.waiting_for_wet_cleaning, F.text.in_(["Да", "Нет"]))
async def process_wet_cleaning(message: Message, state: FSMContext):
    # Если ответ "Да", значит влажная уборка НЕ требуется => True
    is_wet_cleaning_not_required = (message.text == "Да")
    await state.update_data(is_wet_cleaning_not_required=is_wet_cleaning_not_required)
    await message.answer("Оставьте комментарий (или введите '-' для пропуска):")
    await state.set_state(EmployeeStates.waiting_for_open_comment)

@router.message(EmployeeStates.waiting_for_open_comment)
async def process_open_comment(message: Message, state: FSMContext):
    open_comment = message.text if message.text != "-" else ""
    await state.update_data(open_comment=open_comment)
    await message.answer("Отправьте фото начала смены (чек или общий вид):", reply_markup=None)
    await state.set_state(EmployeeStates.waiting_for_photo_start)

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
        
        shift = create_shift(
            db,
            employee_id=employee.id,
            trading_point=data["trading_point"],
            cash_start=data["cash_start"],
            photo_url=photo_url,
            is_light_on=data["is_light_on"],
            is_camera_on=data["is_camera_on"],
            is_display_ok=data["is_display_ok"],
            is_wet_cleaning_not_required=data["is_wet_cleaning_not_required"],
            open_comment=data["open_comment"]
        )
        airtable_data = {
            "employee_id": employee.telegram_id,
            "trading_point": shift.trading_point,
            "cash_start": shift.cash_start,
            "start_time": shift.start_time.isoformat(),
            "photo_url": photo_url,
            "is_light_on": shift.is_light_on,
            "is_camera_on": shift.is_camera_on,
            "is_display_ok": shift.is_display_ok,
            "is_wet_cleaning_not_required": shift.is_wet_cleaning_not_required,
            "open_comment": shift.open_comment
        }
        send_to_airtable("shift_start", airtable_data, compressed_path)
    os.remove(compressed_path)
    await message.answer("Смена начата! Используйте кнопки для перерывов.", reply_markup=get_shift_buttons())
    await state.update_data(shift_id=shift.id)
    await state.set_state(None)
    await state.clear()

@router.message(Command("end_shift"))
async def end_shift_cmd(message: Message, state: FSMContext):
    await state.set_state(None)
    await state.clear()

    if not is_registered_employee(message):
        await message.answer("Вы не зарегистрированы.")
        return
    elif get_registered_employee(message).role == "senior_manager":
        await message.answer("Вы не можете начать смену, так как вы являетесь старшим сотрудником.")
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
        await message.answer("Введите итог (сумма):")
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
    await message.answer("Введите остаток наличных в кассе:")
    await state.set_state(EmployeeStates.waiting_for_balance)

@router.message(EmployeeStates.waiting_for_balance)
async def process_balance(message: Message, state: FSMContext):
    try:
        balance = int(message.text)
        await state.update_data(balance=balance)
        # Переход к недостающим полям (подписки и т.д.)
        await message.answer("Сколько подписок (или '-' если нет):")
        await state.set_state(EmployeeStates.waiting_for_subscriptions)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_subscriptions)
async def process_subscriptions(message: Message, state: FSMContext):
    subscriptions = message.text
    await state.update_data(subscriptions=subscriptions)
    await message.answer("Сколько выдано карт лояльности (или '-' если нет):")
    await state.set_state(EmployeeStates.waiting_for_loyalty_cards_issued)

@router.message(EmployeeStates.waiting_for_loyalty_cards_issued)
async def process_loyalty_cards_issued(message: Message, state: FSMContext):
    loyalty_cards_issued = message.text
    await state.update_data(loyalty_cards_issued=loyalty_cards_issued)
    await message.answer("Инкассация (укажите текст, сумму или '-' если нет):")
    await state.set_state(EmployeeStates.waiting_for_incassation)

@router.message(EmployeeStates.waiting_for_incassation)
async def process_incassation(message: Message, state: FSMContext):
    incassation = message.text
    await state.update_data(incassation=incassation)
    await message.answer("QR (сумма, если нет – укажите '-'):")
    await state.set_state(EmployeeStates.waiting_for_qr)

@router.message(EmployeeStates.waiting_for_qr)
async def process_qr(message: Message, state: FSMContext):
    qr = message.text
    await state.update_data(qr=qr)
    await message.answer("Доставка (если нет, введите '-'):")
    await state.set_state(EmployeeStates.waiting_for_delivery)

@router.message(EmployeeStates.waiting_for_delivery)
async def process_delivery(message: Message, state: FSMContext):
    delivery = message.text
    await state.update_data(delivery=delivery)
    await message.answer("Онлайн заказы (если нет, введите '-'):")
    await state.set_state(EmployeeStates.waiting_for_online_orders)

@router.message(EmployeeStates.waiting_for_online_orders)
async def process_online_orders(message: Message, state: FSMContext):
    online_orders = message.text
    await state.update_data(online_orders=online_orders)
    await message.answer("Брак (если нет, введите '-'):")
    await state.set_state(EmployeeStates.waiting_for_defect)

@router.message(EmployeeStates.waiting_for_defect)
async def process_defect(message: Message, state: FSMContext):
    defect = message.text
    await state.update_data(defect=defect)
    await message.answer("Оставьте комментарий по закрытию (или '-' если нет):")
    await state.set_state(EmployeeStates.waiting_for_close_comment)

@router.message(EmployeeStates.waiting_for_close_comment)
async def process_close_comment(message: Message, state: FSMContext):
    close_comment = message.text if message.text != "-" else ""
    await state.update_data(close_comment=close_comment)
    await message.answer("Отправьте фото окончания смены:", reply_markup=None)
    await state.set_state(EmployeeStates.waiting_for_photo_end)

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
            db,
            shift_id=data["shift_id"],
            cash_income=data["cash_income"],
            cashless_income=data["cashless_income"],
            total=data["total"],
            expenses=data["expenses"],
            balance=data["balance"],
            photo_url=photo_url,
            subscriptions=data["subscriptions"],
            loyalty_cards_issued=data["loyalty_cards_issued"],
            incassation=data["incassation"],
            qr=data["qr"],
            delivery=data["delivery"],
            online_orders=data["online_orders"],
            defect=data["defect"],
            close_comment=data["close_comment"]
        )
        airtable_data = {
            "employee_id": str(message.from_user.id),
            "trading_point": shift.trading_point,
            "cash_income": shift.cash_income,
            "cashless_income": shift.cashless_income,
            "total": shift.total,
            "expenses": shift.expenses,
            "balance": shift.balance,
            "subscriptions": shift.subscriptions,
            "loyalty_cards_issued": shift.loyalty_cards_issued,
            "incassation": shift.incassation,
            "qr": shift.qr,
            "delivery": shift.delivery,
            "online_orders": shift.online_orders,
            "defect": shift.defect,
            "close_comment": shift.close_comment,
            "end_time": shift.end_time.isoformat(),
            "photo_url": photo_url
        }
        send_to_airtable("shift_end", airtable_data, compressed_path)
    os.remove(compressed_path)
    await message.answer("Смена завершена!")
    await state.set_state(None)
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


# Начло првоерки, чистота, выкладка и т.д.

# Чистота
@router.message(Command("perform_check"))
async def perform_check(message: Message, state: FSMContext):
    await state.set_state(None)
    await state.clear()

    if not is_registered_employee(message):
        await message.answer("Вы не зарегистрированы как старший сотрудник.")
        return

    elif not get_registered_employee(message).role == "senior_manager":
        await message.answer("Вы не зарегистрированы как старший сотрудник.")
        return
    
    await message.answer("Торговая точка:", reply_markup=get_trading_points())
    await state.set_state(EmployeeStates.waiting_for_trading_point_perform_check)
    



@router.message(EmployeeStates.waiting_for_trading_point_perform_check, F.text.in_(["Патриарши", "Торговая точка 1", "Торговая точка 2"]))
async def process_trading_perform_check(message: Message, state: FSMContext):
    trading_status = message.text
    await state.update_data(trading_point=trading_status)
    await message.answer("Чистота:", reply_markup=get_cleaning_buttons())
    await state.set_state(EmployeeStates.waiting_for_cleaning)


# Время открытия
@router.message(EmployeeStates.waiting_for_cleaning, F.text.in_(["Чисто", "Требовалась уборка", "Грязно"]))
async def process_cleaning(message: Message, state: FSMContext):
    cleaning_status = message.text
    await state.update_data(cleaning=cleaning_status)
    await message.answer("Введите время открытия:", reply_markup=opening_time_keyboard())
    await state.set_state(EmployeeStates.waiting_for_opening_time)


@router.message(EmployeeStates.waiting_for_opening_time, F.text.in_(["Раньше", "Вовремя", "Позже"]))
async def process_opening_time(message: Message, state: FSMContext):
    opening_time_status = message.text
    await state.update_data(opening_time=opening_time_status)
    await message.answer("Выкладка днем:", reply_markup=layout_keyboard())
    await state.set_state(EmployeeStates.waiting_for_layout_afternoon)

@router.message(EmployeeStates.waiting_for_layout_afternoon, F.text.in_(["Правильная выкладка", "Мелкие исправления", "Переделка в выкладке"]))
async def process_layout_afternoon(message: Message, state: FSMContext):
    layout_status = message.text
    await state.update_data(layout_afternoon=layout_status)
    await message.answer("Выкладка вечером:", reply_markup=layout_keyboard())
    await state.set_state(EmployeeStates.waiting_for_layout_evening)

@router.message(EmployeeStates.waiting_for_layout_evening, F.text.in_(["Правильная выкладка", "Мелкие исправления", "Переделка в выкладке"]))
async def process_layout_evening(message: Message, state: FSMContext):
    layout_status = message.text
    await state.update_data(layout_evening=layout_status)
    await message.answer("Время отходов", reply_markup=waste_time_keyboard())
    await state.set_state(EmployeeStates.waiting_for_waste_time)

@router.message(EmployeeStates.waiting_for_waste_time, F.text.in_(["Соблюдено", "Не соблюдено", "Фактически не превышено"]))
async def process_waste_time(message: Message, state: FSMContext):
    waste_status = message.text
    await state.update_data(waste_time=waste_status)
    await message.answer("Форма сотрудников в порядке?", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_uniform)

@router.message(EmployeeStates.waiting_for_uniform, F.text.in_(["Да", "Нет"]))
async def process_uniform(message: Message, state: FSMContext):
    uniform_status = message.text

    if uniform_status == "Да":
        uniform_status = True
    else:
        uniform_status = False

    data = await state.get_data()

    with SessionLocal() as db:
        employee = get_employee_by_id(db, str(message.from_user.id))
        if employee is None:
            await message.answer("Сотрудник не найден. Вы не зарегистрированы для работы со сменами.")
            await state.clear()
            return
        
        check = create_check(
            db,
            employee_id=message.from_user.id,
            trading_point=data['trading_point'],
            cleaning=data["cleaning"],
            opening=data["opening_time"],
            layout_afternoon=data["layout_afternoon"],
            layout_evening=data["layout_evening"],
            waste_time=data["waste_time"],
            uniform=uniform_status
        )
    
        airtable_data = {
            'employee_id': message.from_user.id,
            'trading_point': data.get('trading_point'),
            'cleaning': data.get('cleaning'),
            'opening_time': data.get('opening_time'),
            'layout_afternoon': data.get('layout_afternoon'),
            'layout_evening': data.get('layout_evening'),
            'waste_time': data.get('waste_time'),
            'uniform': uniform_status
        }

        send_to_airtable("perform_check", airtable_data)
    
    
    
    await message.answer("Проверка завершена. Данные сохранены и отпарвлены в airtable.")
    await state.set_state(None)
    await state.clear()
