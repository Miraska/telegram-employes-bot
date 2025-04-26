from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime
from PIL import Image
import os

from bot.states.employee import EmployeeStates
from bot.keyboards.employee import (
    get_shift_buttons,
    get_trading_points,
    yes_no_keyboard,
    get_cleaning_buttons,
    opening_time_keyboard,
    layout_keyboard,
    waste_time_keyboard,
)
from database.crud import create_shift, get_employee_by_id, create_check
from database.models import SessionLocal, Shift
from services.airtable import send_to_airtable, upload_to_yandex_cloud
from utils.auth import get_registered_employee

router = Router()

def compress_image(input_path: str, output_path: str, max_size=(800, 800), quality=70):
    with Image.open(input_path) as img:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img.save(output_path, format="JPEG", quality=quality)

# Открытие смены
@router.message(Command("start_shift"))
async def start_shift(message: Message, state: FSMContext):
    await state.clear()
    emp = get_registered_employee(message.from_user.id)
    if emp is None:
        return await message.answer("Вы не зарегистрированы. Обратитесь к администратору.")
    if emp.role == "senior_manager":
        return await message.answer("Старшие сотрудники не могут начинать смену.")
    await message.answer("Выберите торговую точку:", reply_markup=get_trading_points())
    await state.set_state(EmployeeStates.waiting_for_trading_point)

@router.callback_query(F.data == "action:start_shift")
async def start_shift_button(callback: CallbackQuery, state: FSMContext):
    with SessionLocal() as db:
        emp = get_employee_by_id(db, callback.from_user.id)
        if emp is None:
            await callback.message.answer("Вы не зарегистрированы. Обратитесь к администратору.")
            await callback.answer()
            return
        if emp.role == "senior_manager":
            await callback.message.answer("Старшие сотрудники не могут начинать смену.")
            await callback.answer()
            return
    await callback.message.answer("Выберите торговую точку:", reply_markup=get_trading_points())
    await state.set_state(EmployeeStates.waiting_for_trading_point)
    await callback.answer()

@router.callback_query(F.data.startswith("trading_point:"), EmployeeStates.waiting_for_trading_point)
async def process_trading_point(callback: CallbackQuery, state: FSMContext):
    tp = callback.data.split(":", 1)[1]
    await state.update_data(trading_point=tp)
    await callback.message.edit_text("Введите сумму наличных на начало дня:", reply_markup=None)
    await state.set_state(EmployeeStates.waiting_for_cash_start)
    await callback.answer()

@router.message(EmployeeStates.waiting_for_cash_start)
async def process_cash_start(message: Message, state: FSMContext):
    try:
        cs = int(message.text)
        await state.update_data(cash_start=cs)
        await message.answer("Подсветка включена? (Да/Нет)", reply_markup=yes_no_keyboard())
        await state.set_state(EmployeeStates.waiting_for_light_on)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.callback_query(F.data.startswith("yes_no:"), EmployeeStates.waiting_for_light_on)
async def process_light_on(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1] == "Да"
    await state.update_data(is_light_on=val)
    await callback.message.edit_text("Камера подключена? (Да/Нет)", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_camera_on)
    await callback.answer()

@router.callback_query(F.data.startswith("yes_no:"), EmployeeStates.waiting_for_camera_on)
async def process_camera_on(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1] == "Да"
    await state.update_data(is_camera_on=val)
    await callback.message.edit_text("Выкладка в норме? (Да/Нет)", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_display_ok)
    await callback.answer()

@router.callback_query(F.data.startswith("yes_no:"), EmployeeStates.waiting_for_display_ok)
async def process_display_ok(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1] == "Да"
    await state.update_data(is_display_ok=val)
    await callback.message.edit_text("Влажная уборка не требуется? (Да/Нет)", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_wet_cleaning)
    await callback.answer()

@router.callback_query(F.data.startswith("yes_no:"), EmployeeStates.waiting_for_wet_cleaning)
async def process_wet_cleaning(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1] == "Да"
    await state.update_data(is_wet_cleaning_not_required=val)
    await callback.message.edit_text("Оставьте комментарий или введите '-' для пропуска:", reply_markup=None)
    await state.set_state(EmployeeStates.waiting_for_open_comment)
    await callback.answer()

@router.message(EmployeeStates.waiting_for_open_comment)
async def process_open_comment(message: Message, state: FSMContext):
    comment = "" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(open_comment=comment)
    await message.answer("Отправьте фото начала смены:")
    await state.set_state(EmployeeStates.waiting_for_photo_start)

@router.message(EmployeeStates.waiting_for_photo_start, F.photo)
async def process_photo_start(message: Message, state: FSMContext, bot: Bot):
    file = await bot.get_file(message.photo[-1].file_id)
    tmp = f"/tmp/{message.from_user.id}.jpg"
    comp = f"/tmp/{message.from_user.id}_c.jpg"
    await bot.download_file(file.file_path, tmp)
    compress_image(tmp, comp)
    os.remove(tmp)

    data = await state.get_data()
    with SessionLocal() as db:
        emp = get_employee_by_id(db, message.from_user.id)
        if not emp:
            await message.answer("Сотрудник не найден.")
            os.remove(comp)
            await state.clear()
            return
        url = upload_to_yandex_cloud(comp)
        shift = create_shift(
            db,
            employee_id=emp.id,
            trading_point=data["trading_point"],
            cash_start=data["cash_start"],
            photo_url=url,
            is_light_on=data["is_light_on"],
            is_camera_on=data["is_camera_on"],
            is_display_ok=data["is_display_ok"],
            is_wet_cleaning_not_required=data["is_wet_cleaning_not_required"],
            open_comment=data["open_comment"],
        )
        msg = await message.answer("Смена начата!", reply_markup=get_shift_buttons())
        shift.break_message_id = msg.message_id
        db.commit()
        send_to_airtable("shift_start", {
            "employee_id": emp.telegram_id,
            "trading_point": shift.trading_point,
            "cash_start": shift.cash_start,
            "start_time": shift.start_time.isoformat(),
            "photo_url": url,
            "open_comment": shift.open_comment,
        })
    os.remove(comp)
    await state.update_data(shift_id=shift.id)
    await state.clear()

# Перерывы
@router.callback_query(F.data.startswith("shift:"))
async def process_shift_buttons(callback: CallbackQuery):
    action = callback.data.split(":", 1)[1]
    with SessionLocal() as db:
        emp = get_employee_by_id(db, callback.from_user.id)
        if not emp:
            return await callback.message.answer("Вы не зарегистрированы.")
        sh = db.query(Shift).filter(Shift.employee_id == emp.id, Shift.end_time.is_(None)).first()
        if not sh:
            return await callback.message.answer("Смена не начата.")
        if action == "Отошел":
            if sh.break_start_at:
                return await callback.message.answer("Вы уже на перерыве.")
            sh.break_start_at = datetime.utcnow()
            db.commit()
            await callback.message.answer("Перерыв начат.")
        elif action == "Пришел":
            if not sh.break_start_at:
                return await callback.message.answer("Перерыв не начат.")
            dur = int((datetime.utcnow() - sh.break_start_at).total_seconds() / 60)
            sh.total_break_minutes += dur
            sh.break_start_at = None
            db.commit()
            await callback.message.answer(f"Перерыв окончен. Длительность: {dur} мин.")
    await callback.answer()

# Завершение смены
@router.message(Command("end_shift"))
async def end_shift_cmd(message: Message, state: FSMContext):
    await state.clear()
    emp = get_registered_employee(message.from_user.id)
    if emp is None:
        return await message.answer("Вы не зарегистрированы.")
    if emp.role == "senior_manager":
        return await message.answer("Старшие сотрудники не могут завершать смену.")
    with SessionLocal() as db:
        sh = db.query(Shift).filter(Shift.employee_id == emp.id, Shift.end_time.is_(None)).first()
        if not sh:
            return await message.answer("Активная смена не найдена.")
    await state.update_data(shift_id=sh.id)
    await message.answer("Введите приход наличных:")
    await state.set_state(EmployeeStates.waiting_for_cash_income)

@router.callback_query(F.data == "action:end_shift")
async def end_shift_button(callback: CallbackQuery, state: FSMContext):
    with SessionLocal() as db:
        emp = get_employee_by_id(db, callback.from_user.id)
        if emp is None:
            await callback.message.answer("Вы не зарегистрированы.")
            await callback.answer()
            return
        if emp.role == "senior_manager":
            await callback.message.answer("Старшие сотрудники не могут завершать смену.")
            await callback.answer()
            return
        sh = db.query(Shift).filter(Shift.employee_id == emp.id, Shift.end_time.is_(None)).first()
        if not sh:
            await callback.message.answer("Активная смена не найдена.")
            await callback.answer()
            return
        await state.update_data(shift_id=sh.id)
    await callback.message.answer("Введите приход наличных:")
    await state.set_state(EmployeeStates.waiting_for_cash_income)
    await callback.answer()

@router.message(EmployeeStates.waiting_for_cash_income)
async def process_cash_income(message: Message, state: FSMContext):
    try:
        ci = int(message.text)
        await state.update_data(cash_income=ci)
        await message.answer("Введите безналичный доход:")
        await state.set_state(EmployeeStates.waiting_for_cashless_income)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_cashless_income)
async def process_total(message: Message, state: FSMContext):
    try:
        cashless_income = int(message.text)
        await state.update_data(cashless_income=cashless_income)
        await message.answer("Введите расходы:")
        await state.set_state(EmployeeStates.waiting_for_expenses)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_expenses)
async def process_expenses(message: Message, state: FSMContext):
    try:
        expenses = int(message.text)
        await state.update_data(expenses=expenses)
        await message.answer("Введите количество подписок:")
        await state.set_state(EmployeeStates.waiting_for_subscriptions)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_subscriptions)
async def process_subscriptions(message: Message, state: FSMContext):
    try:
        subs = int(message.text)
        await state.update_data(subscriptions=subs)
        await message.answer("Введите количество выданных карт лояльности:")
        await state.set_state(EmployeeStates.waiting_for_loyalty_cards_issued)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_loyalty_cards_issued)
async def process_loyalty_cards_issued(message: Message, state: FSMContext):
    try:
        lci = int(message.text)
        await state.update_data(loyalty_cards_issued=lci)
        await message.answer("Введите сумму инкассации:")
        await state.set_state(EmployeeStates.waiting_for_incassation)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_incassation)
async def process_incassation(message: Message, state: FSMContext):
    try:
        inc = int(message.text)
        await state.update_data(incassation=inc)
        await message.answer("Введите сумму по QR:")
        await state.set_state(EmployeeStates.waiting_for_qr)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_qr)
async def process_qr(message: Message, state: FSMContext):
    try:
        qr = int(message.text)
        await state.update_data(qr=qr)
        await message.answer("Введите сумму доставки:")
        await state.set_state(EmployeeStates.waiting_for_delivery)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_delivery)
async def process_delivery(message: Message, state: FSMContext):
    try:
        delivery = int(message.text)
        await state.update_data(delivery=delivery)
        await message.answer("Введите количество онлайн-заказов:")
        await state.set_state(EmployeeStates.waiting_for_online_orders)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_online_orders)
async def process_online_orders(message: Message, state: FSMContext):
    try:
        oo = int(message.text)
        await state.update_data(online_orders=oo)
        await message.answer("Введите сумму брака:")
        await state.set_state(EmployeeStates.waiting_for_defect)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_defect)
async def process_defect(message: Message, state: FSMContext):
    try:
        defect = int(message.text)
        await state.update_data(defect=defect)
        await message.answer("Оставьте комментарий или введите '-' для пропуска:")
        await state.set_state(EmployeeStates.waiting_for_close_comment)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.message(EmployeeStates.waiting_for_close_comment)
async def process_close_comment(message: Message, state: FSMContext):
    comment = "" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(close_comment=comment)
    await message.answer("Отправьте фото конца смены:")
    await state.set_state(EmployeeStates.waiting_for_photo_end)

@router.message(EmployeeStates.waiting_for_photo_end, F.photo)
async def process_photo_end(message: Message, state: FSMContext, bot: Bot):
    file = await bot.get_file(message.photo[-1].file_id)
    tmp = f"/tmp/{message.from_user.id}_end.jpg"
    comp = f"/tmp/{message.from_user.id}_end_c.jpg"
    await bot.download_file(file.file_path, tmp)
    compress_image(tmp, comp)
    os.remove(tmp)

    data = await state.get_data()
    with SessionLocal() as db:
        sh = db.get(Shift, data["shift_id"])
        url = upload_to_yandex_cloud(comp)
        
        # Добавляем расчет общего времени перерыва, включая текущий перерыв если он активен
        total_break_minutes = sh.total_break_minutes
        
        # Если перерыв активен на момент закрытия смены, добавляем его длительность
        if sh.break_start_at:
            current_break_duration = int((datetime.utcnow() - sh.break_start_at).total_seconds() / 60)
            total_break_minutes += current_break_duration
            sh.break_start_at = None
        
        sh.end_time = datetime.utcnow()
        sh.cash_income = data["cash_income"]
        sh.cashless_income = data["cashless_income"]
        sh.expenses = data["expenses"]
        sh.subscriptions = data["subscriptions"]
        sh.loyalty_cards_issued = data["loyalty_cards_issued"]
        sh.incassation = data["incassation"]
        sh.qr = data["qr"]
        sh.delivery = data["delivery"]
        sh.online_orders = data["online_orders"]
        sh.defect = data["defect"]
        sh.close_comment = data["close_comment"]
        sh.photo_url_end = url
        sh.total_break_minutes = total_break_minutes
        
        db.commit()
        
        send_to_airtable("shift_end", {
            "shift_id": sh.id,
            "employee_id": message.from_user.id,
            "cash_income": sh.cash_income,
            "cashless_income": sh.cashless_income,
            "expenses": sh.expenses,
            "subscriptions": sh.subscriptions,
            "loyalty_cards_issued": sh.loyalty_cards_issued,
            "incassation": sh.incassation,
            "qr": sh.qr,
            "delivery": sh.delivery,
            "online_orders": sh.online_orders,
            "defect": sh.defect,
            "close_comment": sh.close_comment,
            "end_time": sh.end_time.isoformat(),
            "photo_url_end": url,
            "total_break_minutes": total_break_minutes,
            "trading_point": sh.trading_point,
        })
        
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sh.break_message_id,
            text="Смена завершена.",
            reply_markup=None
        )
    os.remove(comp)
    await message.answer(f"Смена завершена. Общее время перерыва: {total_break_minutes} мин.")
    await state.clear()

# Проверка
@router.message(Command("perform_check"))
async def perform_check(message: Message, state: FSMContext):
    print(f"Message ID: {message.from_user.id}")
    await state.clear()
    emp = get_registered_employee(message.from_user.id)
    print(f"Employee: {emp}, Role: {emp.role if emp else 'None'}")
    if emp is None:
        print("Сотрудник не найден в базе данных.")
        await message.answer("Вы не зарегистрированы. Обратитесь к администратору.")
        return
    if emp.role != "senior_manager":
        print(f"Неправильная роль: {emp.role}")
        await message.answer("Вы не зарегистрированы как старший сотрудник.")
        return
    await message.answer("Торговая точка:", reply_markup=get_trading_points())
    await state.set_state(EmployeeStates.waiting_for_trading_point_perform_check)

@router.callback_query(F.data == "action:perform_check")
async def perform_check_button(callback: CallbackQuery, state: FSMContext):
    with SessionLocal() as db:
        emp = get_employee_by_id(db, callback.from_user.id)
        if emp is None:
            await callback.message.answer("Вы не зарегистрированы. Обратитесь к администратору.")
            await callback.answer()
            return
        if emp.role != "senior_manager":
            await callback.message.answer("Вы не зарегистрированы как старший сотрудник.")
            await callback.answer()
            return
    await callback.message.answer("Торговая точка:", reply_markup=get_trading_points())
    await state.set_state(EmployeeStates.waiting_for_trading_point_perform_check)
    await callback.answer()

@router.callback_query(F.data.startswith("trading_point:"), EmployeeStates.waiting_for_trading_point_perform_check)
async def process_trading_perform_check(callback: CallbackQuery, state: FSMContext):
    tp = callback.data.split(":", 1)[1]
    await state.update_data(trading_point=tp)
    await callback.message.edit_text("Чистота:", reply_markup=get_cleaning_buttons())
    await state.set_state(EmployeeStates.waiting_for_cleaning)
    await callback.answer()

@router.callback_query(F.data.startswith("cleaning:"), EmployeeStates.waiting_for_cleaning)
async def process_cleaning(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    await state.update_data(cleaning=val)
    await callback.message.edit_text("Введите время открытия:", reply_markup=opening_time_keyboard())
    await state.set_state(EmployeeStates.waiting_for_opening_time)
    await callback.answer()

@router.callback_query(F.data.startswith("opening_time:"), EmployeeStates.waiting_for_opening_time)
async def process_opening_time(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    await state.update_data(opening_time=val)
    await callback.message.edit_text("Выкладка днем:", reply_markup=layout_keyboard())
    await state.set_state(EmployeeStates.waiting_for_layout_afternoon)
    await callback.answer()

@router.callback_query(F.data.startswith("layout:"), EmployeeStates.waiting_for_layout_afternoon)
async def process_layout_afternoon(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    await state.update_data(layout_afternoon=val)
    await callback.message.edit_text("Выкладка вечером:", reply_markup=layout_keyboard())
    await state.set_state(EmployeeStates.waiting_for_layout_evening)
    await callback.answer()

@router.callback_query(F.data.startswith("layout:"), EmployeeStates.waiting_for_layout_evening)
async def process_layout_evening(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    await state.update_data(layout_evening=val)
    await callback.message.edit_text("Время отходов:", reply_markup=waste_time_keyboard())
    await state.set_state(EmployeeStates.waiting_for_waste_time)
    await callback.answer()

@router.callback_query(F.data.startswith("waste_time:"), EmployeeStates.waiting_for_waste_time)
async def process_waste_time(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    await state.update_data(waste_time=val)
    await callback.message.edit_text("Форма сотрудников в порядке?", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_uniform)
    await callback.answer()

@router.callback_query(F.data.startswith("yes_no:"), EmployeeStates.waiting_for_uniform)
async def process_uniform(callback: CallbackQuery, state: FSMContext):
    ok = callback.data.split(":", 1)[1] == "Да"
    data = await state.get_data()
    with SessionLocal() as db:
        emp = get_employee_by_id(db, callback.from_user.id)
        if not emp:
            await callback.message.answer("Сотрудник не найден.")
            await state.clear()
            return
        create_check(
            db,
            employee_id=emp.id,
            trading_point=emp.trading_point,
            cleaning=data["cleaning"],
            opening=data["opening_time"],
            layout_afternoon=data["layout_afternoon"],
            layout_evening=data["layout_evening"],
            waste_time=data["waste_time"],
            uniform=ok,
        )
        send_to_airtable("perform_check", {
            "employee_id": emp.telegram_id,
            "trading_point": emp.trading_point,
            "cleaning": data["cleaning"],
            "opening_time": data["opening_time"],
            "layout_afternoon": data["layout_afternoon"],
            "layout_evening": data["layout_evening"],
            "waste_time": data["waste_time"],
            "uniform": ok,
        })
    await callback.message.answer("Проверка завершена.")
    await state.clear()
    await callback.answer()