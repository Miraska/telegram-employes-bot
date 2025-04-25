from aiogram import Router, F, Bot, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from bot.states.employee import EmployeeStates
from bot.keyboards.employee import get_shift_buttons, get_trading_points, yes_no_keyboard, get_cleaning_buttons, layout_keyboard, opening_time_keyboard, waste_time_keyboard, get_employee_menu, get_senior_manager_menu
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
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
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

@router.callback_query(F.data.startswith("trading_point:"), EmployeeStates.waiting_for_trading_point)
async def process_trading_point(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_trading_point)
    await state.update_data(state_stack=state_stack)
    trading_point = callback_query.data.split(":")[1]
    await state.update_data(trading_point=trading_point)
    await callback_query.message.edit_text("Введите сумму наличных на начало дня:")
    await state.set_state(EmployeeStates.waiting_for_cash_start)
    await callback_query.answer()

@router.message(EmployeeStates.waiting_for_cash_start)
async def process_cash_start(message: Message, state: FSMContext):
    try:
        cash_start = int(message.text)
        await state.update_data(cash_start=cash_start)
        await message.answer("Подсветка включена? (Да/Нет)", reply_markup=yes_no_keyboard())
        await state.set_state(EmployeeStates.waiting_for_light_on)
    except ValueError:
        await message.answer("Введите корректное число.")

@router.callback_query(F.data.startswith("yes_no:"), EmployeeStates.waiting_for_light_on)
async def process_light_on(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_light_on)
    await state.update_data(state_stack=state_stack)
    is_light_on = (callback_query.data.split(":")[1] == "Да")
    await state.update_data(is_light_on=is_light_on)
    await callback_query.message.edit_text("Камера подключена? (Да/Нет)", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_camera_on)
    await callback_query.answer()

@router.callback_query(F.data.startswith("yes_no:"), EmployeeStates.waiting_for_camera_on)
async def process_camera_on(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_camera_on)
    await state.update_data(state_stack=state_stack)
    is_camera_on = (callback_query.data.split(":")[1] == "Да")
    await state.update_data(is_camera_on=is_camera_on)
    await callback_query.message.edit_text("Выкладка в норме? (Да/Нет)", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_display_ok)
    await callback_query.answer()

@router.callback_query(F.data.startswith("yes_no:"), EmployeeStates.waiting_for_display_ok)
async def process_display_ok(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_display_ok)
    await state.update_data(state_stack=state_stack)
    is_display_ok = (callback_query.data.split(":")[1] == "Да")
    await state.update_data(is_display_ok=is_display_ok)
    await callback_query.message.edit_text("Влажная уборка не требуется? (Да/Нет)", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_wet_cleaning)
    await callback_query.answer()

@router.callback_query(F.data.startswith("yes_no:"), EmployeeStates.waiting_for_wet_cleaning)
async def process_wet_cleaning(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_wet_cleaning)
    await state.update_data(state_stack=state_stack)
    is_wet_cleaning_not_required = (callback_query.data.split(":")[1] == "Да")
    await state.update_data(is_wet_cleaning_not_required=is_wet_cleaning_not_required)
    await callback_query.message.edit_text("Оставьте комментарий (или введите '-' для пропуска):")
    await state.set_state(EmployeeStates.waiting_for_open_comment)
    await callback_query.answer()

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
            await message.answer("Сотрудник не найден.")
            os.remove(compressed_path)
            await state.clear()
            return
        photo_url = upload_to_yandex_cloud(compressed_path)
        shift = create_shift(db, employee_id=employee.id, trading_point=data["trading_point"], 
                             cash_start=data["cash_start"], photo_url=photo_url,
                             is_light_on=data["is_light_on"], is_camera_on=data["is_camera_on"], 
                             is_display_ok=data["is_display_ok"],
                             is_wet_cleaning_not_required=data["is_wet_cleaning_not_required"], 
                             open_comment=data["open_comment"])
        msg = await message.answer("Смена начата! Используйте кнопки для перерывов.", reply_markup=get_shift_buttons())
        shift.break_message_id = msg.message_id
        db.commit()
        airtable_data = {
            "employee_id": employee.telegram_id, "trading_point": shift.trading_point, 
            "cash_start": shift.cash_start, "start_time": shift.start_time.isoformat(), 
            "photo_url": photo_url, "is_light_on": shift.is_light_on,
            "is_camera_on": shift.is_camera_on, "is_display_ok": shift.is_display_ok,
            "is_wet_cleaning_not_required": shift.is_wet_cleaning_not_required, 
            "open_comment": shift.open_comment
        }
        send_to_airtable("shift_start", airtable_data, compressed_path)
    os.remove(compressed_path)
    await state.update_data(shift_id=shift.id)
    await state.clear()

@router.callback_query(F.data.startswith("shift:"))
async def process_shift_buttons(callback_query: CallbackQuery):
    action = callback_query.data.split(":")[1]
    with SessionLocal() as db:
        employee = get_employee_by_id(db, str(callback_query.from_user.id))
        if not employee:
            await callback_query.message.answer("Вы не зарегистрированы.")
            return
        shift = db.query(Shift).filter(Shift.employee_id == employee.id, Shift.end_time == None).first()
        if not shift:
            await callback_query.message.answer("Смена не начата.")
            return
        if action == "Отошел":
            if shift.break_start_at:
                await callback_query.message.answer("Вы уже на перерыве.")
            else:
                shift.break_start_at = datetime.utcnow()
                db.commit()
                await callback_query.message.answer("Перерыв начат.")
        elif action == "Пришел":
            if not shift.break_start_at:
                await callback_query.message.answer("Перерыв не начат.")
            else:
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
                await callback_query.message.answer(f"Перерыв окончен. Длительность: {break_duration} мин.")
    await callback_query.answer()

@router.message(Command("end_shift"))
async def end_shift_cmd(message: Message, state: FSMContext):
    await state.set_state(None)
    await state.clear()
    if not is_registered_employee(message):
        await message.answer("Вы не зарегистрированы.")
        return
    elif get_registered_employee(message).role == "senior_manager":
        await message.answer("Вы не можете завершить смену, так как вы старший сотрудник.")
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
async def process_cash_income(message: Message, state: FSMContext, bot: Bot):
    try:
        cash_income = int(message.text)
        data = await state.get_data()
        shift_id = data["shift_id"]
        with SessionLocal() as db:
            shift = db.query(Shift).filter(Shift.id == shift_id).first()
            if not shift:
                await message.answer("Смена не найдена.")
                await state.clear()
                return
            shift.cash_income = cash_income
            shift.end_time = datetime.utcnow()
            db.commit()
            if shift.break_message_id:
                try:
                    await bot.delete_message(chat_id=message.chat.id, message_id=shift.break_message_id)
                except Exception as e:
                    print(f"Не удалось удалить сообщение: {e}")
            airtable_data = {
                "shift_id": shift.id,
                "cash_income": shift.cash_income,
                "end_time": shift.end_time.isoformat()
            }
            send_to_airtable("shift_end", airtable_data)
        await message.answer("Смена завершена.", reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Начать новую смену", callback_data="action:start_shift")]
            ]
        ))
        await state.clear()
    except ValueError:
        await message.answer("Введите корректное число.")

@router.callback_query(F.data == "action:start_shift")
async def restart_shift(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()  # Удаляем сообщение с кнопками
    await start_shift(callback_query.message, state)
    await callback_query.answer()

@router.message(Command("perform_check"))
async def perform_check(message: Message, state: FSMContext):
    await state.set_state(None)
    await state.clear()
    if not get_registered_employee(message):
        await message.answer("Вы не зарегистрированы как старший сотрудник.")
        return

    elif not get_registered_employee(message).role == "manager":
        await message.answer("Вы не зарегистрированы как старший сотрудник.")
        return

    await message.answer("Торговая точка:", reply_markup=get_trading_points())
    await state.set_state(EmployeeStates.waiting_for_trading_point_perform_check)

@router.callback_query(F.data.startswith("trading_point:"), EmployeeStates.waiting_for_trading_point_perform_check)
async def process_trading_perform_check(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_trading_point_perform_check)
    await state.update_data(state_stack=state_stack)
    trading_point = callback_query.data.split(":")[1]
    await state.update_data(trading_point=trading_point)
    await callback_query.message.edit_text("Чистота:", reply_markup=get_cleaning_buttons())
    await state.set_state(EmployeeStates.waiting_for_cleaning)
    await callback_query.answer()

@router.callback_query(F.data.startswith("cleaning:"), EmployeeStates.waiting_for_cleaning)
async def process_cleaning(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_cleaning)
    await state.update_data(state_stack=state_stack)
    cleaning_status = callback_query.data.split(":")[1]
    await state.update_data(cleaning=cleaning_status)
    await callback_query.message.edit_text("Введите время открытия:", reply_markup=opening_time_keyboard())
    await state.set_state(EmployeeStates.waiting_for_opening_time)
    await callback_query.answer()

@router.callback_query(F.data.startswith("opening_time:"), EmployeeStates.waiting_for_opening_time)
async def process_opening_time(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_opening_time)
    await state.update_data(state_stack=state_stack)
    opening_time_status = callback_query.data.split(":")[1]
    await state.update_data(opening_time=opening_time_status)
    await callback_query.message.edit_text("Выкладка днем:", reply_markup=layout_keyboard())
    await state.set_state(EmployeeStates.waiting_for_layout_afternoon)
    await callback_query.answer()

@router.callback_query(F.data.startswith("layout:"), EmployeeStates.waiting_for_layout_afternoon)
async def process_layout_afternoon(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_layout_afternoon)
    await state.update_data(state_stack=state_stack)
    layout_status = callback_query.data.split(":")[1]
    await state.update_data(layout_afternoon=layout_status)
    await callback_query.message.edit_text("Выкладка вечером:", reply_markup=layout_keyboard())
    await state.set_state(EmployeeStates.waiting_for_layout_evening)
    await callback_query.answer()

@router.callback_query(F.data.startswith("layout:"), EmployeeStates.waiting_for_layout_evening)
async def process_layout_evening(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_layout_evening)
    await state.update_data(state_stack=state_stack)
    layout_status = callback_query.data.split(":")[1]
    await state.update_data(layout_evening=layout_status)
    await callback_query.message.edit_text("Время отходов:", reply_markup=waste_time_keyboard())
    await state.set_state(EmployeeStates.waiting_for_waste_time)
    await callback_query.answer()

@router.callback_query(F.data.startswith("waste_time:"), EmployeeStates.waiting_for_waste_time)
async def process_waste_time(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_waste_time)
    await state.update_data(state_stack=state_stack)
    waste_status = callback_query.data.split(":")[1]
    await state.update_data(waste_time=waste_status)
    await callback_query.message.edit_text("Форма сотрудников в порядке?", reply_markup=yes_no_keyboard())
    await state.set_state(EmployeeStates.waiting_for_uniform)
    await callback_query.answer()

@router.callback_query(F.data.startswith("yes_no:"), EmployeeStates.waiting_for_uniform)
async def process_uniform(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    state_stack.append(EmployeeStates.waiting_for_uniform)
    await state.update_data(state_stack=state_stack)
    uniform_status = callback_query.data.split(":")[1] == "Да"
    data = await state.get_data()
    with SessionLocal() as db:
        employee = get_employee_by_id(db, str(callback_query.from_user.id))
        if employee is None:
            await callback_query.message.answer("Сотрудник не найден.")
            await state.clear()
            return
        check = create_check(db, employee_id=callback_query.from_user.id, trading_point=data['trading_point'], 
                             cleaning=data["cleaning"], opening=data["opening_time"], 
                             layout_afternoon=data["layout_afternoon"], layout_evening=data["layout_evening"],
                             waste_time=data["waste_time"], uniform=uniform_status)
        airtable_data = {
            'employee_id': callback_query.from_user.id, 'trading_point': data.get('trading_point'), 
            'cleaning': data.get('cleaning'), 'opening_time': data.get('opening_time'), 
            'layout_afternoon': data.get('layout_afternoon'), 'layout_evening': data.get('layout_evening'),
            'waste_time': data.get('waste_time'), 'uniform': uniform_status
        }
        send_to_airtable("perform_check", airtable_data)
    await callback_query.message.answer("Проверка завершена. Данные сохранены и отправлены в Airtable.", 
                                        reply_markup=InlineKeyboardMarkup(
                                            inline_keyboard=[
                                                [InlineKeyboardButton(text="Выполнить новую проверку", callback_data="action:perform_check")]
                                            ]
                                        ))
    await state.clear()
    await callback_query.answer()

@router.callback_query(F.data == "action:perform_check")
async def restart_check(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()  # Удаляем сообщение с кнопками
    await perform_check(callback_query.message, state)
    await callback_query.answer()

@router.callback_query(F.data == "back")
async def process_back(callback_query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    if state_stack:
        previous_state = state_stack.pop()
        await state.update_data(state_stack=state_stack)
        await state.set_state(previous_state)
        if previous_state == EmployeeStates.waiting_for_trading_point:
            await callback_query.message.edit_text("Выберите торговую точку:", reply_markup=get_trading_points())
        elif previous_state == EmployeeStates.waiting_for_light_on:
            await callback_query.message.edit_text("Подсветка включена? (Да/Нет)", reply_markup=yes_no_keyboard())
        elif previous_state == EmployeeStates.waiting_for_camera_on:
            await callback_query.message.edit_text("Камера подключена? (Да/Нет)", reply_markup=yes_no_keyboard())
        elif previous_state == EmployeeStates.waiting_for_display_ok:
            await callback_query.message.edit_text("Выкладка в норме? (Да/Нет)", reply_markup=yes_no_keyboard())
        elif previous_state == EmployeeStates.waiting_for_wet_cleaning:
            await callback_query.message.edit_text("Влажная уборка не требуется? (Да/Нет)", reply_markup=yes_no_keyboard())
        elif previous_state == EmployeeStates.waiting_for_trading_point_perform_check:
            await callback_query.message.edit_text("Торговая точка:", reply_markup=get_trading_points())
        elif previous_state == EmployeeStates.waiting_for_cleaning:
            await callback_query.message.edit_text("Чистота:", reply_markup=get_cleaning_buttons())
        elif previous_state == EmployeeStates.waiting_for_opening_time:
            await callback_query.message.edit_text("Введите время открытия:", reply_markup=opening_time_keyboard())
        elif previous_state == EmployeeStates.waiting_for_layout_afternoon:
            await callback_query.message.edit_text("Выкладка днем:", reply_markup=layout_keyboard())
        elif previous_state == EmployeeStates.waiting_for_layout_evening:
            await callback_query.message.edit_text("Выкладка вечером:", reply_markup=layout_keyboard())
        elif previous_state == EmployeeStates.waiting_for_waste_time:
            await callback_query.message.edit_text("Время отходов:", reply_markup=waste_time_keyboard())
        elif previous_state == EmployeeStates.waiting_for_uniform:
            await callback_query.message.edit_text("Форма сотрудников в порядке?", reply_markup=yes_no_keyboard())
    else:
        await callback_query.message.edit_text("Нет предыдущего шага.")
    await callback_query.answer()