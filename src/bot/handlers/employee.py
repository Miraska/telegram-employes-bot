from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime
from PIL import Image
import tempfile
import os

from bot.states.employee import EmployeeStates
from bot.keyboards.employee import (
    get_end_shift_confirmation_keyboard,
    get_end_shift_edit_keyboard,
    get_perform_check_confirmation_keyboard,
    get_perform_check_edit_keyboard,
    get_shift_in_buttons,
    get_shift_out_buttons,
    get_start_shift_confirmation_keyboard,
    get_start_shift_edit_keyboard,
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
from .common import get_main_menu

router = Router()


FIELD_NAMES = {
    # Поля для открытия смены
    "trading_point": "Торговая точка",
    "cash_start": "Сумма наличных на начало дня",
    "is_light_on": "Подсветка включена",
    "is_camera_on": "Камера подключена",
    "is_display_ok": "Выкладка в норме",
    "is_wet_cleaning_not_required": "Влажная уборка не требуется",
    "open_comment": "Комментарий",
    "photo_url_start": "Фото начала смены",
    # Поля для закрытия смены
    "total_income": "Приход всего",
    "cash_income": "Наличные",
    "cashless_income": "Безналичные",
    "qr_payments": "QR-оплаты",
    "returns": "Возвраты",
    "cash_balance": "Остаток наличных в кассе",
    "salary_advance": "В счёт ЗП",
    "incassation_decision": "Была ли инкассация",
    "incassation_amount": "Сумма инкассации",
    "logistics_expenses": "Расходы: Логистика",
    "household_expenses": "Расходы: Хозяйственные нужды",
    "other_expenses": "Расходы: Иные",
    "online_delivery": "Онлайн-доставка",
    "loyalty_cards_issued": "Выдано карт лояльности",
    "subscriptions": "Подписки",
    "malfunctions": "Неисправности / поломки",
    "requested_products": "Необходимый товар",
    "photo_url_end": "Фото конца смены",
    # Поля для проверок
    "cleaning": "Чистота",
    "opening_time": "Время открытия",
    "layout_afternoon": "Выкладка днем",
    "layout_evening": "Выкладка вечером",
    "waste_time": "Время отходов",
    "uniform": "Форма",
}


def get_temp_path(filename: str) -> str:
    """Возвращает временный путь для файла, работающий на всех ОС"""
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, filename)


# Функция для сжатия изображения
def compress_image(input_path: str, output_path: str, max_size=(800, 800), quality=70):
    with Image.open(input_path) as img:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img.save(output_path, format="JPEG", quality=quality)


# Начало смены через команду
@router.message(Command("start_shift"))
async def start_shift(message: Message, state: FSMContext):
    await state.clear()
    emp = get_registered_employee(message.from_user.id)
    if emp is None:
        return await message.answer(
            "Вы не зарегистрированы. Обратитесь к администратору."
        )
    if emp.role == "senior_manager":
        return await message.answer("Старшие сотрудники не могут начинать смену.")
    await message.answer("Выберите торговую точку:", reply_markup=get_trading_points())
    await state.set_state(EmployeeStates.waiting_for_trading_point)


# Начало смены через кнопку
@router.callback_query(F.data == "action:start_shift")
async def start_shift_button(callback: CallbackQuery, state: FSMContext):
    with SessionLocal() as db:
        emp = get_employee_by_id(db, callback.from_user.id)
        if emp is None:
            await callback.message.answer(
                "Вы не зарегистрированы. Обратитесь к администратору."
            )
            await callback.answer()
            return
        if emp.role == "senior_manager":
            await callback.message.answer("Старшие сотрудники не могут начинать смену.")
            await callback.answer()
            return
    await callback.message.edit_text(
        "Выберите торговую точку:", reply_markup=get_trading_points()
    )
    await state.set_state(EmployeeStates.waiting_for_trading_point)
    await callback.answer()


# Обработка выбора торговой точки
@router.callback_query(
    F.data.startswith("trading_point:"), EmployeeStates.waiting_for_trading_point
)
async def process_trading_point(callback: CallbackQuery, state: FSMContext):
    tp = callback.data.split(":", 1)[1]
    await state.update_data(trading_point=tp)
    data = await state.get_data()
    required_keys = [
        "cash_start",
        "is_light_on",
        "is_camera_on",
        "is_display_ok",
        "is_wet_cleaning_not_required",
        "open_comment",
        "photo_url_start",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_start_shift)
        summary = (
            "Проверьте данные начала смены:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Сумма наличных: {data['cash_start']}\n"
            f"Подсветка: {'Да' if data['is_light_on'] else 'Нет'}\n"
            f"Камера: {'Да' if data['is_camera_on'] else 'Нет'}\n"
            f"Выкладка: {'Да' if data['is_display_ok'] else 'Нет'}\n"
            f"Влажная уборка не требуется: {'Да' if data['is_wet_cleaning_not_required'] else 'Нет'}\n"
            f"Комментарий: {data['open_comment']}\n"
            "Фото: [прикреплено]"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_start_shift_confirmation_keyboard()
        )
    else:
        await callback.message.edit_text("Введите сумму наличных на начало дня:")
        await state.set_state(EmployeeStates.waiting_for_cash_start)
    await callback.answer()


# Обработка суммы наличных в начале смены
@router.message(EmployeeStates.waiting_for_cash_start)
async def process_cash_start(message: Message, state: FSMContext):
    try:
        cs = int(message.text)
        await state.update_data(cash_start=cs)
        data = await state.get_data()
        required_keys = [
            "trading_point",
            "is_light_on",
            "is_camera_on",
            "is_display_ok",
            "is_wet_cleaning_not_required",
            "open_comment",
            "photo_url_start",
        ]
        if all(key in data for key in required_keys):
            await state.set_state(EmployeeStates.confirming_start_shift)
            summary = (
                "Проверьте данные начала смены:\n"
                f"Торговая точка: {data['trading_point']}\n"
                f"Сумма наличных: {data['cash_start']}\n"
                f"Подсветка: {'Да' if data['is_light_on'] else 'Нет'}\n"
                f"Камера: {'Да' if data['is_camera_on'] else 'Нет'}\n"
                f"Выкладка: {'Да' if data['is_display_ok'] else 'Нет'}\n"
                f"Влажная уборка не требуется: {'Да' if data['is_wet_cleaning_not_required'] else 'Нет'}\n"
                f"Комментарий: {data['open_comment']}\n"
                "Фото: [прикреплено]"
            )
            await message.answer(
                summary, reply_markup=get_start_shift_confirmation_keyboard()
            )
        else:
            await message.answer(
                "Подсветка включена? (Да/Нет)", reply_markup=yes_no_keyboard()
            )
            await state.set_state(EmployeeStates.waiting_for_light_on)
    except ValueError:
        await message.answer("Введите корректное число.")


# Обработка статуса подсветки
@router.callback_query(
    F.data.startswith("yes_no:"), EmployeeStates.waiting_for_light_on
)
async def process_light_on(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1] == "Да"
    await state.update_data(is_light_on=val)
    data = await state.get_data()
    required_keys = [
        "trading_point",
        "cash_start",
        "is_camera_on",
        "is_display_ok",
        "is_wet_cleaning_not_required",
        "open_comment",
        "photo_url_start",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_start_shift)
        summary = (
            "Проверьте данные начала смены:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Сумма наличных: {data['cash_start']}\n"
            f"Подсветка: {'Да' if data['is_light_on'] else 'Нет'}\n"
            f"Камера: {'Да' if data['is_camera_on'] else 'Нет'}\n"
            f"Выкладка: {'Да' if data['is_display_ok'] else 'Нет'}\n"
            f"Влажная уборка не требуется: {'Да' if data['is_wet_cleaning_not_required'] else 'Нет'}\n"
            f"Комментарий: {data['open_comment']}\n"
            "Фото: [прикреплено]"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_start_shift_confirmation_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Камера подключена? (Да/Нет)", reply_markup=yes_no_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_camera_on)
    await callback.answer()


# Обработка статуса камеры
@router.callback_query(
    F.data.startswith("yes_no:"), EmployeeStates.waiting_for_camera_on
)
async def process_camera_on(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1] == "Да"
    await state.update_data(is_camera_on=val)
    data = await state.get_data()
    required_keys = [
        "trading_point",
        "cash_start",
        "is_light_on",
        "is_display_ok",
        "is_wet_cleaning_not_required",
        "open_comment",
        "photo_url_start",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_start_shift)
        summary = (
            "Проверьте данные начала смены:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Сумма наличных: {data['cash_start']}\n"
            f"Подсветка: {'Да' if data['is_light_on'] else 'Нет'}\n"
            f"Камера: {'Да' if data['is_camera_on'] else 'Нет'}\n"
            f"Выкладка: {'Да' if data['is_display_ok'] else 'Нет'}\n"
            f"Влажная уборка не требуется: {'Да' if data['is_wet_cleaning_not_required'] else 'Нет'}\n"
            f"Комментарий: {data['open_comment']}\n"
            "Фото: [прикреплено]"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_start_shift_confirmation_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Выкладка в норме? (Да/Нет)", reply_markup=yes_no_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_display_ok)
    await callback.answer()


# Обработка статуса выкладки
@router.callback_query(
    F.data.startswith("yes_no:"), EmployeeStates.waiting_for_display_ok
)
async def process_display_ok(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1] == "Да"
    await state.update_data(is_display_ok=val)
    data = await state.get_data()
    required_keys = [
        "trading_point",
        "cash_start",
        "is_light_on",
        "is_camera_on",
        "is_wet_cleaning_not_required",
        "open_comment",
        "photo_url_start",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_start_shift)
        summary = (
            "Проверьте данные начала смены:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Сумма наличных: {data['cash_start']}\n"
            f"Подсветка: {'Да' if data['is_light_on'] else 'Нет'}\n"
            f"Камера: {'Да' if data['is_camera_on'] else 'Нет'}\n"
            f"Выкладка: {'Да' if data['is_display_ok'] else 'Нет'}\n"
            f"Влажная уборка не требуется: {'Да' if data['is_wet_cleaning_not_required'] else 'Нет'}\n"
            f"Комментарий: {data['open_comment']}\n"
            "Фото: [прикреплено]"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_start_shift_confirmation_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Влажная уборка не требуется? (Да/Нет)", reply_markup=yes_no_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_wet_cleaning)
    await callback.answer()


# Обработка статуса влажной уборки
@router.callback_query(
    F.data.startswith("yes_no:"), EmployeeStates.waiting_for_wet_cleaning
)
async def process_wet_cleaning(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1] == "Да"
    await state.update_data(is_wet_cleaning_not_required=val)
    data = await state.get_data()
    required_keys = [
        "trading_point",
        "cash_start",
        "is_light_on",
        "is_camera_on",
        "is_display_ok",
        "open_comment",
        "photo_url_start",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_start_shift)
        summary = (
            "Проверьте данные начала смены:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Сумма наличных: {data['cash_start']}\n"
            f"Подсветка: {'Да' if data['is_light_on'] else 'Нет'}\n"
            f"Камера: {'Да' if data['is_camera_on'] else 'Нет'}\n"
            f"Выкладка: {'Да' if data['is_display_ok'] else 'Нет'}\n"
            f"Влажная уборка не требуется: {'Да' if data['is_wet_cleaning_not_required'] else 'Нет'}\n"
            f"Комментарий: {data['open_comment']}\n"
            "Фото: [прикреплено]"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_start_shift_confirmation_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Оставьте комментарий или введите '-' для пропуска:"
        )
        await state.set_state(EmployeeStates.waiting_for_open_comment)
    await callback.answer()


# Обработка комментария к открытию смены
@router.message(EmployeeStates.waiting_for_open_comment)
async def process_open_comment(message: Message, state: FSMContext):
    comment = "" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(open_comment=comment)
    data = await state.get_data()
    required_keys = [
        "trading_point",
        "cash_start",
        "is_light_on",
        "is_camera_on",
        "is_display_ok",
        "is_wet_cleaning_not_required",
        "photo_url_start",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_start_shift)
        summary = (
            "Проверьте данные начала смены:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Сумма наличных: {data['cash_start']}\n"
            f"Подсветка: {'Да' if data['is_light_on'] else 'Нет'}\n"
            f"Камера: {'Да' if data['is_camera_on'] else 'Нет'}\n"
            f"Выкладка: {'Да' if data['is_display_ok'] else 'Нет'}\n"
            f"Влажная уборка не требуется: {'Да' if data['is_wet_cleaning_not_required'] else 'Нет'}\n"
            f"Комментарий: {data['open_comment']}\n"
            "Фото: [прикреплено]"
        )
        await message.answer(
            summary, reply_markup=get_start_shift_confirmation_keyboard()
        )
    else:
        await message.answer("Отправьте фото начала смены:")
        await state.set_state(EmployeeStates.waiting_for_photo_start)


# Обработка фото начала смены
@router.message(EmployeeStates.waiting_for_photo_start, F.photo)
async def process_photo_start(message: Message, state: FSMContext, bot: Bot):
    file = await bot.get_file(message.photo[-1].file_id)

    # Используем функцию get_temp_path для кроссплатформенного пути
    tmp = get_temp_path(f"{message.from_user.id}.jpg")
    comp = get_temp_path(f"{message.from_user.id}_c.jpg")

    try:
        await bot.download_file(file.file_path, tmp)
        compress_image(tmp, comp)

        # Удаляем временные файлы только если они существуют
        if os.path.exists(tmp):
            os.remove(tmp)

        url = upload_to_yandex_cloud(comp)
        await state.update_data(photo_url_start=url)

        if os.path.exists(comp):
            os.remove(comp)

        data = await state.get_data()
        await state.set_state(EmployeeStates.confirming_start_shift)
        summary = (
            "Проверьте данные начала смены:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Сумма наличных: {data['cash_start']}\n"
            f"Подсветка: {'Да' if data['is_light_on'] else 'Нет'}\n"
            f"Камера: {'Да' if data['is_camera_on'] else 'Нет'}\n"
            f"Выкладка: {'Да' if data['is_display_ok'] else 'Нет'}\n"
            f"Влажная уборка не требуется: {'Да' if data['is_wet_cleaning_not_required'] else 'Нет'}\n"
            f"Комментарий: {data['open_comment']}\n"
            "Фото: [прикреплено]"
        )
        await message.answer(
            summary, reply_markup=get_start_shift_confirmation_keyboard()
        )

    except Exception as e:
        await message.answer(f"Ошибка при обработке фото: {str(e)}")
        # Удаляем временные файлы в случае ошибки
        if os.path.exists(tmp):
            os.remove(tmp)
        if os.path.exists(comp):
            os.remove(comp)


# Обработка подтверждения начала смены
@router.callback_query(
    F.data.startswith("confirm_start_shift:"), EmployeeStates.confirming_start_shift
)
async def process_confirm_start_shift(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":", 1)[1]
    data = await state.get_data()
    if action == "yes":
        with SessionLocal() as db:
            emp = get_employee_by_id(db, callback.from_user.id)
            if not emp:
                await callback.message.answer("Сотрудник не найден.")
                await state.clear()
                return
            shift = create_shift(
                db,
                employee_id=emp.id,
                trading_point=data["trading_point"],
                cash_start=data["cash_start"],
                photo_url=data["photo_url_start"],
                open_comment=data["open_comment"],
                is_light_on=data["is_light_on"],
                is_camera_on=data["is_camera_on"],
                is_display_ok=data["is_display_ok"],
                is_wet_cleaning_not_required=data["is_wet_cleaning_not_required"],
            )
            msg = await callback.message.edit_text(
                "Смена начата!", reply_markup=get_shift_out_buttons()
            )
            shift.break_message_id = msg.message_id
            db.commit()
            send_to_airtable(
                "shift_start",
                {
                    "employee_id": emp.telegram_id,
                    "trading_point": shift.trading_point,
                    "cash_start": shift.cash_start,
                    "start_time": shift.start_time.isoformat(),
                    "photo_url": data["photo_url_start"],
                    "open_comment": shift.open_comment,
                    "is_light_on": data["is_light_on"],
                    "is_camera_on": data["is_camera_on"],
                    "is_display_ok": data["is_display_ok"],
                    "is_wet_cleaning_not_required": data[
                        "is_wet_cleaning_not_required"
                    ],
                },
            )
        await state.clear()
    elif action == "edit":
        await state.set_state(EmployeeStates.editing_start_shift)
        await callback.message.edit_text(
            "Выберите, что хотите отредактировать:",
            reply_markup=get_start_shift_edit_keyboard(),
        )
    elif action == "cancel":
        await callback.message.edit_text(
            "Процесс начала смены отменен.",
            reply_markup=get_main_menu(callback.message),
        )
        await state.clear()
    await callback.answer()


# Обработка редактирования начала смены
@router.callback_query(
    F.data.startswith("edit_start_shift:"), EmployeeStates.editing_start_shift
)
async def process_edit_start_shift(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":", 1)[1]
    if field == "trading_point":
        await callback.message.edit_text(
            "Выберите новую торговую точку:", reply_markup=get_trading_points()
        )
        await state.set_state(EmployeeStates.waiting_for_trading_point)
    elif field == "cash_start":
        await callback.message.edit_text("Введите новую сумму наличных на начало дня:")
        await state.set_state(EmployeeStates.waiting_for_cash_start)
    elif field == "is_light_on":
        await callback.message.edit_text(
            "Подсветка включена? (Да/Нет)", reply_markup=yes_no_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_light_on)
    elif field == "is_camera_on":
        await callback.message.edit_text(
            "Камера подключена? (Да/Нет)", reply_markup=yes_no_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_camera_on)
    elif field == "is_display_ok":
        await callback.message.edit_text(
            "Выкладка в норме? (Да/Нет)", reply_markup=yes_no_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_display_ok)
    elif field == "is_wet_cleaning_not_required":
        await callback.message.edit_text(
            "Влажная уборка не требуется? (Да/Нет)", reply_markup=yes_no_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_wet_cleaning)
    elif field == "open_comment":
        await callback.message.edit_text(
            "Оставьте новый комментарий или введите '-' для пропуска:"
        )
        await state.set_state(EmployeeStates.waiting_for_open_comment)
    elif field == "photo_start":
        await callback.message.edit_text("Отправьте новое фото начала смены:")
        await state.set_state(EmployeeStates.waiting_for_photo_start)
    elif field == "confirm":
        await state.set_state(EmployeeStates.confirming_start_shift)
        data = await state.get_data()
        summary = (
            "Проверьте данные начала смены:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Сумма наличных: {data['cash_start']}\n"
            f"Подсветка: {'Да' if data['is_light_on'] else 'Нет'}\n"
            f"Камера: {'Да' if data['is_camera_on'] else 'Нет'}\n"
            f"Выкладка: {'Да' if data['is_display_ok'] else 'Нет'}\n"
            f"Влажная уборка не требуется: {'Да' if data['is_wet_cleaning_not_required'] else 'Нет'}\n"
            f"Комментарий: {data['open_comment']}\n"
            "Фото: [прикреплено]"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_start_shift_confirmation_keyboard()
        )
    await callback.answer()


# Обработка кнопок перерыва
@router.callback_query(F.data.startswith("shift:"))
async def process_shift_buttons(callback: CallbackQuery):
    action = callback.data.split(":", 1)[1]
    with SessionLocal() as db:
        emp = get_employee_by_id(db, callback.from_user.id)
        if not emp:
            return await callback.message.answer("Вы не зарегистрированы.")
        sh = (
            db.query(Shift)
            .filter(Shift.employee_id == emp.id, Shift.end_time.is_(None))
            .first()
        )
        if not sh:
            return await callback.message.answer("Смена не начата.")
        if action == "Отошел":
            if sh.break_start_at:
                return await callback.message.answer("Вы уже на перерыве.")
            sh.break_start_at = datetime.utcnow()
            db.commit()
            await callback.message.edit_text(
                "Перерыв начат.", reply_markup=get_shift_in_buttons()
            )
        elif action == "Пришел":
            if not sh.break_start_at:
                return await callback.message.answer("Перерыв не начат.")
            dur = int((datetime.utcnow() - sh.break_start_at).total_seconds() / 60)
            sh.total_break_minutes += dur
            sh.break_start_at = None
            db.commit()
            await callback.message.edit_text(
                f"Перерыв окончен. Длительность: {dur} мин.",
                reply_markup=get_shift_out_buttons(),
            )
    await callback.answer()


# Завершение смены через команду
@router.message(Command("end_shift"))
async def end_shift_cmd(message: Message, state: FSMContext):
    await state.clear()
    emp = get_registered_employee(message.from_user.id)
    if emp is None:
        return await message.answer("Вы не зарегистрированы.")
    if emp.role == "senior_manager":
        return await message.answer("Старшие сотрудники не могут завершать смену.")
    with SessionLocal() as db:
        sh = (
            db.query(Shift)
            .filter(Shift.employee_id == emp.id, Shift.end_time.is_(None))
            .first()
        )
        if not sh:
            return await message.answer("Активная смена не найдена.")
        await state.update_data(
            shift_id=sh.id, trading_point=sh.trading_point, full_name=emp.full_name
        )
    await message.answer("Введите приход всего:")
    await state.set_state(EmployeeStates.waiting_for_total_income)


# Завершение смены через кнопку
@router.callback_query(F.data == "action:end_shift")
async def end_shift_button(callback: CallbackQuery, state: FSMContext):
    with SessionLocal() as db:
        emp = get_employee_by_id(db, callback.from_user.id)
        if emp is None:
            await callback.message.answer("Вы не зарегистрированы.")
            await callback.answer()
            return
        if emp.role == "senior_manager":
            await callback.message.answer(
                "Старшие сотрудники не могут завершать смену."
            )
            await callback.answer()
            return
        sh = (
            db.query(Shift)
            .filter(Shift.employee_id == emp.id, Shift.end_time.is_(None))
            .first()
        )
        if not sh:
            await callback.message.answer("Активная смена не найдена.")
            await callback.answer()
            return
        await state.update_data(
            shift_id=sh.id, trading_point=sh.trading_point, full_name=emp.full_name
        )
    await callback.message.edit_text("Введите приход всего:")
    await state.set_state(EmployeeStates.waiting_for_total_income)
    await callback.answer()


# Приход всего
@router.message(EmployeeStates.waiting_for_total_income)
async def process_total_income(message: Message, state: FSMContext):
    try:
        total_income = int(message.text)
        await state.update_data(total_income=total_income)
        await message.answer("Введите наличные:")
        await state.set_state(EmployeeStates.waiting_for_cash_income)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Наличные
@router.message(EmployeeStates.waiting_for_cash_income)
async def process_cash_income(message: Message, state: FSMContext):
    try:
        cash_income = int(message.text)
        await state.update_data(cash_income=cash_income)
        await message.answer("Введите безналичные:")
        await state.set_state(EmployeeStates.waiting_for_cashless_income)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Безналичные
@router.message(EmployeeStates.waiting_for_cashless_income)
async def process_cashless_income(message: Message, state: FSMContext):
    try:
        cashless_income = int(message.text)
        await state.update_data(cashless_income=cashless_income)
        await message.answer("Введите QR-оплаты:")
        await state.set_state(EmployeeStates.waiting_for_qr_payments)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# QR-оплаты
@router.message(EmployeeStates.waiting_for_qr_payments)
async def process_qr_payments(message: Message, state: FSMContext):
    try:
        qr_payments = int(message.text)
        await state.update_data(qr_payments=qr_payments)
        await message.answer("Введите возвраты (0 если нет):")
        await state.set_state(EmployeeStates.waiting_for_returns)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Возвраты
@router.message(EmployeeStates.waiting_for_returns)
async def process_returns(message: Message, state: FSMContext):
    try:
        returns = int(message.text)
        await state.update_data(returns=returns)
        await message.answer("Введите остаток наличных в кассе:")
        await state.set_state(EmployeeStates.waiting_for_cash_balance)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Остаток наличных
@router.message(EmployeeStates.waiting_for_cash_balance)
async def process_cash_balance(message: Message, state: FSMContext):
    try:
        cash_balance = int(message.text)
        await state.update_data(cash_balance=cash_balance)
        await message.answer("Введите сумму в счёт ЗП (0 если нет):")
        await state.set_state(EmployeeStates.waiting_for_salary_advance)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# В счёт ЗП
@router.message(EmployeeStates.waiting_for_salary_advance)
async def process_salary_advance(message: Message, state: FSMContext):
    try:
        salary_advance = int(message.text)
        await state.update_data(salary_advance=salary_advance)
        await message.answer("Была ли инкассация?", reply_markup=yes_no_keyboard())
        await state.set_state(EmployeeStates.waiting_for_incassation_decision)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Решение по инкассации
@router.callback_query(
    F.data.startswith("yes_no:"), EmployeeStates.waiting_for_incassation_decision
)
async def process_incassation_decision(callback: CallbackQuery, state: FSMContext):
    decision = callback.data.split(":", 1)[1] == "Да"
    await state.update_data(incassation_decision=decision)
    if decision:
        await callback.message.edit_text("Введите сумму инкассации:")
        await state.set_state(EmployeeStates.waiting_for_incassation_amount)
    else:
        await callback.message.edit_text("Введите расходы на логистику (0 если нет):")
        await state.set_state(EmployeeStates.waiting_for_logistics_expenses)
    await callback.answer()


# Сумма инкассации
@router.message(EmployeeStates.waiting_for_incassation_amount)
async def process_incassation_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        await state.update_data(incassation_amount=amount)
        await message.answer("Введите расходы на логистику (0 если нет):")
        await state.set_state(EmployeeStates.waiting_for_logistics_expenses)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Расходы: Логистика
@router.message(EmployeeStates.waiting_for_logistics_expenses)
async def process_logistics_expenses(message: Message, state: FSMContext):
    try:
        logistics_expenses = int(message.text)
        await state.update_data(logistics_expenses=logistics_expenses)
        await message.answer("Введите расходы на хозяйственные нужды (0 если нет):")
        await state.set_state(EmployeeStates.waiting_for_household_expenses)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Расходы: Хозяйственные нужды
@router.message(EmployeeStates.waiting_for_household_expenses)
async def process_household_expenses(message: Message, state: FSMContext):
    try:
        household_expenses = int(message.text)
        await state.update_data(household_expenses=household_expenses)
        await message.answer("Введите иные расходы (0 если нет):")
        await state.set_state(EmployeeStates.waiting_for_other_expenses)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Расходы: Иные
@router.message(EmployeeStates.waiting_for_other_expenses)
async def process_other_expenses(message: Message, state: FSMContext):
    try:
        other_expenses = int(message.text)
        await state.update_data(other_expenses=other_expenses)
        await message.answer("Введите сумму онлайн-доставки (0 если нет):")
        await state.set_state(EmployeeStates.waiting_for_online_delivery)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Онлайн-доставка
@router.message(EmployeeStates.waiting_for_online_delivery)
async def process_online_delivery(message: Message, state: FSMContext):
    try:
        online_delivery = int(message.text)
        await state.update_data(online_delivery=online_delivery)
        await message.answer(
            "Введите количество выданных карт лояльности (0 если нет):"
        )
        await state.set_state(EmployeeStates.waiting_for_loyalty_cards_issued)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Карты лояльности
@router.message(EmployeeStates.waiting_for_loyalty_cards_issued)
async def process_loyalty_cards_issued(message: Message, state: FSMContext):
    try:
        loyalty_cards_issued = int(message.text)
        await state.update_data(loyalty_cards_issued=loyalty_cards_issued)
        await message.answer("Введите количество подписок (0 если нет):")
        await state.set_state(EmployeeStates.waiting_for_subscriptions)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Подписки
@router.message(EmployeeStates.waiting_for_subscriptions)
async def process_subscriptions(message: Message, state: FSMContext):
    try:
        subscriptions = int(message.text)
        await state.update_data(subscriptions=subscriptions)
        await message.answer("Опишите неисправности / поломки на точке (или 'нет'):")
        await state.set_state(EmployeeStates.waiting_for_malfunctions)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")


# Неисправности
@router.message(EmployeeStates.waiting_for_malfunctions)
async def process_malfunctions(message: Message, state: FSMContext):
    malfunctions = message.text.strip()
    await state.update_data(malfunctions=malfunctions)
    await message.answer(
        "Укажите необходимый товар, который спрашивали клиенты (или 'нет'):"
    )
    await state.set_state(EmployeeStates.waiting_for_requested_products)


# Необходимый товар
@router.message(EmployeeStates.waiting_for_requested_products)
async def process_requested_products(message: Message, state: FSMContext):
    requested_products = message.text.strip()
    await state.update_data(requested_products=requested_products)
    await message.answer("Отправьте фото конца смены:")
    await state.set_state(EmployeeStates.waiting_for_photo_end)


# Фото конца смены
@router.message(EmployeeStates.waiting_for_photo_end, F.photo)
async def process_photo_end(message: Message, state: FSMContext, bot: Bot):
    file = await bot.get_file(message.photo[-1].file_id)
    tmp = get_temp_path(f"{message.from_user.id}_end.jpg")
    comp = get_temp_path(f"{message.from_user.id}_end_c.jpg")
    try:
        await bot.download_file(file.file_path, tmp)
        compress_image(tmp, comp)
        if os.path.exists(tmp):
            os.remove(tmp)
        url = upload_to_yandex_cloud(comp)
        await state.update_data(photo_url_end=url)
        if os.path.exists(comp):
            os.remove(comp)
        data = await state.get_data()
        await state.set_state(EmployeeStates.confirming_end_shift)
        summary = (
            "ОТЧЁТ О ЗАКРЫТИИ СМЕНЫ\n\n"
            f"Дата: {datetime.now().strftime('%d.%m.%Y')}\n"
            f"Время закрытия: {datetime.now().strftime('%H:%M')}\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"ФИО сдающего смену: {data['full_name']}\n\n"
            "Финансовый отчёт:\n"
            f"- Приход всего: {data['total_income']}\n"
            f"- Наличные: {data['cash_income']}\n"
            f"- Безналичные: {data['cashless_income']}\n"
            f"- QR-оплаты: {data['qr_payments']}\n"
            f"- Возвраты: {data['returns']}\n"
            f"- Остаток наличных в кассе: {data['cash_balance']}\n"
            f"- В счёт ЗП: {data['salary_advance']}\n\n"
            f"Инкассация: {'да' if data['incassation_decision'] else 'нет'}\n"
            f"Сумма инкассации: {data.get('incassation_amount', '-')}\n\n"
            "Расходы:\n"
            f"- Логистика: {data['logistics_expenses']}\n"
            f"- Хозяйственные нужды: {data['household_expenses']}\n"
            f"- Иные расходы: {data['other_expenses']}\n\n"
            "Дополнительно:\n"
            f"- Онлайн-доставка: {data['online_delivery']}\n"
            f"- Выдано карт лояльности: {data['loyalty_cards_issued']}\n"
            f"- Подписки: {data['subscriptions']}\n\n"
            "Техлист:\n"
            f"- Неисправности / поломки на точке: {data['malfunctions']}\n"
            f"- Необходимый товар, который спрашивали клиенты: {data['requested_products']}\n\n"
            "Фото: [прикреплено]"
        )
        await message.answer(
            summary, reply_markup=get_end_shift_confirmation_keyboard()
        )
    except Exception as e:
        await message.answer(f"Ошибка при обработке фото: {str(e)}")
        if os.path.exists(tmp):
            os.remove(tmp)
        if os.path.exists(comp):
            os.remove(comp)


# Подтверждение завершения смены
@router.callback_query(
    F.data.startswith("confirm_end_shift:"), EmployeeStates.confirming_end_shift
)
async def process_confirm_end_shift(
    callback: CallbackQuery, state: FSMContext, bot: Bot
):
    action = callback.data.split(":", 1)[1]
    data = await state.get_data()
    if action == "yes":
        with SessionLocal() as db:
            sh = db.get(Shift, data["shift_id"])
            total_break_minutes = sh.total_break_minutes
            if sh.break_start_at:
                current_break_duration = int(
                    (datetime.utcnow() - sh.break_start_at).total_seconds() / 60
                )
                total_break_minutes += current_break_duration
                sh.break_start_at = None
            sh.end_time = datetime.utcnow()
            sh.total = data["total_income"]
            sh.cash_income = data["cash_income"]
            sh.cashless_income = data["cashless_income"]
            sh.qr = data["qr_payments"]
            sh.returns = data["returns"]
            sh.balance = data["cash_balance"]
            sh.salary_advance = data["salary_advance"]
            sh.incassation = str(data["incassation_decision"])
            sh.incassation_amount = data.get("incassation_amount", 0)
            sh.logistics_expenses = data["logistics_expenses"]
            sh.household_expenses = data["household_expenses"]
            sh.other_expenses = data["other_expenses"]
            sh.online_delivery = data["online_delivery"]
            sh.loyalty_cards_issued = str(data["loyalty_cards_issued"])
            sh.subscriptions = str(data["subscriptions"])
            sh.malfunctions = data["malfunctions"]
            sh.requested_products = data["requested_products"]
            sh.photo_url_end = data["photo_url_end"]
            sh.total_break_minutes = total_break_minutes
            db.commit()
            send_to_airtable(
                "shift_end",
                {
                    "shift_id": sh.id,
                    "employee_id": callback.from_user.id,
                    "total_income": sh.total,
                    "cash_income": sh.cash_income,
                    "cashless_income": sh.cashless_income,
                    "qr_payments": sh.qr,
                    "returns": sh.returns,
                    "cash_balance": sh.balance,
                    "salary_advance": sh.salary_advance,
                    "incassation_decision": sh.incassation,
                    "incassation_amount": sh.incassation_amount,
                    "logistics_expenses": sh.logistics_expenses,
                    "household_expenses": sh.household_expenses,
                    "other_expenses": sh.other_expenses,
                    "online_delivery": sh.online_delivery,
                    "loyalty_cards_issued": sh.loyalty_cards_issued,
                    "subscriptions": sh.subscriptions,
                    "malfunctions": sh.malfunctions,
                    "requested_products": sh.requested_products,
                    "end_time": sh.end_time.isoformat(),
                    "photo_url_end": sh.photo_url_end,
                    "total_break_minutes": total_break_minutes,
                    "trading_point": sh.trading_point,
                },
            )
            await bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=sh.break_message_id,
                text="Смена завершена.",
                reply_markup=None,
            )
        await callback.message.edit_text(
            f"Смена завершена. Общее время перерыва: {total_break_minutes} мин.",
            reply_markup=get_main_menu(callback.message),
        )
        await state.clear()
    elif action == "edit":
        await state.set_state(EmployeeStates.editing_end_shift)
        await callback.message.edit_text(
            "Выберите, что хотите отредактировать:",
            reply_markup=get_end_shift_edit_keyboard(),
        )
    elif action == "cancel":
        await callback.message.edit_text(
            "Процесс завершения смены отменен.",
            reply_markup=get_main_menu(callback.message),
        )
        await state.clear()
    await callback.answer()


# Редактирование завершения смены
@router.callback_query(
    F.data.startswith("edit_end_shift:"), EmployeeStates.editing_end_shift
)
async def process_edit_end_shift(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":", 1)[1]
    if field == "confirm":
        await state.set_state(EmployeeStates.confirming_end_shift)
        data = await state.get_data()
        summary = (
            "ОТЧЁТ О ЗАКРЫТИИ СМЕНЫ\n\n"
            f"Дата: {datetime.now().strftime('%d.%m.%Y')}\n"
            f"Время закрытия: {datetime.now().strftime('%H:%M')}\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"ФИО сдающего смену: {data['full_name']}\n\n"
            "Финансовый отчёт:\n"
            f"- Приход всего: {data['total_income']}\n"
            f"- Наличные: {data['cash_income']}\n"
            f"- Безналичные: {data['cashless_income']}\n"
            f"- QR-оплаты: {data['qr_payments']}\n"
            f"- Возвраты: {data['returns']}\n"
            f"- Остаток наличных в кассе: {data['cash_balance']}\n"
            f"- В счёт ЗП: {data['salary_advance']}\n\n"
            f"Инкассация: {'да' if data['incassation_decision'] else 'нет'}\n"
            f"Сумма инкассации: {data.get('incassation_amount', '-')}\n\n"
            "Расходы:\n"
            f"- Логистика: {data['logistics_expenses']}\n"
            f"- Хозяйственные нужды: {data['household_expenses']}\n"
            f"- Иные расходы: {data['other_expenses']}\n\n"
            "Дополнительно:\n"
            f"- Онлайн-доставка: {data['online_delivery']}\n"
            f"- Выдано карт лояльности: {data['loyalty_cards_issued']}\n"
            f"- Подписки: {data['subscriptions']}\n\n"
            "Техлист:\n"
            f"- Неисправности / поломки на точке: {data['malfunctions']}\n"
            f"- Необходимый товар, который спрашивали клиенты: {data['requested_products']}\n\n"
            "Фото: [прикреплено]"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_end_shift_confirmation_keyboard()
        )
    else:
        # Сохраняем название редактируемого поля в FSM
        await state.update_data(editing_field=field)
        if field == "photo_end":
            await callback.message.edit_text("Отправьте новое фото конца смены:")
        elif field == "incassation_decision":
            await callback.message.edit_text(
                "Была ли инкассация?", reply_markup=yes_no_keyboard()
            )
        elif field == "malfunctions" or field == "requested_products":
            await callback.message.edit_text(
                f"Введите новое значение для {FIELD_NAMES[field]} (или 'нет'):"
            )
        else:
            await callback.message.edit_text(f"Введите новое значение для {FIELD_NAMES[field]}:")
        await state.set_state(EmployeeStates.editing_field)
    await callback.answer()


@router.message(EmployeeStates.editing_field)
async def process_editing_field(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    field = data.get("editing_field")

    if field == "photo_end":
        if message.photo:
            file = await bot.get_file(message.photo[-1].file_id)
            tmp = get_temp_path(f"{message.from_user.id}_end.jpg")
            comp = get_temp_path(f"{message.from_user.id}_end_c.jpg")
            try:
                await bot.download_file(file.file_path, tmp)
                compress_image(tmp, comp)
                if os.path.exists(tmp):
                    os.remove(tmp)
                url = upload_to_yandex_cloud(comp)
                await state.update_data(photo_url_end=url)
                if os.path.exists(comp):
                    os.remove(comp)
                await message.answer("Фото обновлено.")
            except Exception as e:
                await message.answer(f"Ошибка при обработке фото: {str(e)}")
                if os.path.exists(tmp):
                    os.remove(tmp)
                if os.path.exists(comp):
                    os.remove(comp)
                return
        else:
            await message.answer("Пожалуйста, отправьте фото.")
            return
    else:
        value = message.text.strip()
        if field == "incassation_decision":
            value = value.lower() == "да"
            await state.update_data(incassation_decision=value)
            if not value:
                await state.update_data(
                    incassation_amount=0
                )  # Сбрасываем сумму инкассации, если её не было
            await message.answer("Значение обновлено.")
        elif field in [
            "total_income",
            "cash_income",
            "cashless_income",
            "qr_payments",
            "returns",
            "cash_balance",
            "salary_advance",
            "incassation_amount",
            "logistics_expenses",
            "household_expenses",
            "other_expenses",
            "online_delivery",
            "loyalty_cards_issued",
            "subscriptions",
        ]:
            try:
                value = int(value)
                await state.update_data({field: value})
                await message.answer("Значение обновлено.")
            except ValueError:
                await message.answer("Пожалуйста, введите корректное число.")
                return
        else:  # Текстовые поля: malfunctions, requested_products
            await state.update_data({field: value})
            await message.answer("Значение обновлено.")

    # Возвращаем пользователя к меню редактирования
    await state.set_state(EmployeeStates.editing_end_shift)
    await message.answer(
        "Выберите, что хотите отредактировать:",
        reply_markup=get_end_shift_edit_keyboard(),
    )


# Начало проверки через команду
@router.message(Command("perform_check"))
async def perform_check(message: Message, state: FSMContext):
    await state.clear()
    emp = get_registered_employee(message.from_user.id)
    if emp is None:
        await message.answer("Вы не зарегистрированы. Обратитесь к администратору.")
        return
    if emp.role != "senior_manager":
        await message.answer("Вы не зарегистрированы как старший сотрудник.")
        return
    await message.answer("Торговая точка:", reply_markup=get_trading_points())
    await state.set_state(EmployeeStates.waiting_for_trading_point_perform_check)


# Начало проверки через кнопку
@router.callback_query(F.data == "action:perform_check")
async def perform_check_button(callback: CallbackQuery, state: FSMContext):
    with SessionLocal() as db:
        emp = get_employee_by_id(db, callback.from_user.id)
        if emp is None:
            await callback.message.answer(
                "Вы не зарегистрированы. Обратитесь к администратору."
            )
            await callback.answer()
            return
        if emp.role != "senior_manager":
            await callback.message.answer(
                "Вы не зарегистрированы как старший сотрудник."
            )
            await callback.answer()
            return
    await callback.message.edit_text(
        "Торговая точка:", reply_markup=get_trading_points()
    )
    await state.set_state(EmployeeStates.waiting_for_trading_point_perform_check)
    await callback.answer()


# Обработка торговой точки для проверки
@router.callback_query(
    F.data.startswith("trading_point:"),
    EmployeeStates.waiting_for_trading_point_perform_check,
)
async def process_trading_perform_check(callback: CallbackQuery, state: FSMContext):
    tp = callback.data.split(":", 1)[1]
    await state.update_data(trading_point=tp)
    data = await state.get_data()
    required_keys = [
        "cleaning",
        "opening_time",
        "layout_afternoon",
        "layout_evening",
        "waste_time",
        "uniform",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_perform_check)
        summary = (
            "Проверьте данные проверки:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Чистота: {data['cleaning']}\n"
            f"Время открытия: {data['opening_time']}\n"
            f"Выкладка днем: {data['layout_afternoon']}\n"
            f"Выкладка вечером: {data['layout_evening']}\n"
            f"Время отходов: {data['waste_time']}\n"
            f"Форма: {'Да' if data['uniform'] else 'Нет'}"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_perform_check_confirmation_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Чистота:", reply_markup=get_cleaning_buttons()
        )
        await state.set_state(EmployeeStates.waiting_for_cleaning)
    await callback.answer()


# Обработка уровня чистоты
@router.callback_query(
    F.data.startswith("cleaning:"), EmployeeStates.waiting_for_cleaning
)
async def process_cleaning(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    await state.update_data(cleaning=val)
    data = await state.get_data()
    required_keys = [
        "trading_point",
        "opening_time",
        "layout_afternoon",
        "layout_evening",
        "waste_time",
        "uniform",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_perform_check)
        summary = (
            "Проверьте данные проверки:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Чистота: {data['cleaning']}\n"
            f"Время открытия: {data['opening_time']}\n"
            f"Выкладка днем: {data['layout_afternoon']}\n"
            f"Выкладка вечером: {data['layout_evening']}\n"
            f"Время отходов: {data['waste_time']}\n"
            f"Форма: {'Да' if data['uniform'] else 'Нет'}"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_perform_check_confirmation_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Введите время открытия:", reply_markup=opening_time_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_opening_time)
    await callback.answer()


# Обработка времени открытия
@router.callback_query(
    F.data.startswith("opening_time:"), EmployeeStates.waiting_for_opening_time
)
async def process_opening_time(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    await state.update_data(opening_time=val)
    data = await state.get_data()
    required_keys = [
        "trading_point",
        "cleaning",
        "layout_afternoon",
        "layout_evening",
        "waste_time",
        "uniform",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_perform_check)
        summary = (
            "Проверьте данные проверки:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Чистота: {data['cleaning']}\n"
            f"Время открытия: {data['opening_time']}\n"
            f"Выкладка днем: {data['layout_afternoon']}\n"
            f"Выкладка вечером: {data['layout_evening']}\n"
            f"Время отходов: {data['waste_time']}\n"
            f"Форма: {'Да' if data['uniform'] else 'Нет'}"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_perform_check_confirmation_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Выкладка днем:", reply_markup=layout_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_layout_afternoon)
    await callback.answer()


# Обработка выкладки днем
@router.callback_query(
    F.data.startswith("layout:"), EmployeeStates.waiting_for_layout_afternoon
)
async def process_layout_afternoon(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    await state.update_data(layout_afternoon=val)
    data = await state.get_data()
    required_keys = [
        "trading_point",
        "cleaning",
        "opening_time",
        "layout_evening",
        "waste_time",
        "uniform",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_perform_check)
        summary = (
            "Проверьте данные проверки:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Чистота: {data['cleaning']}\n"
            f"Время открытия: {data['opening_time']}\n"
            f"Выкладка днем: {data['layout_afternoon']}\n"
            f"Выкладка вечером: {data['layout_evening']}\n"
            f"Время отходов: {data['waste_time']}\n"
            f"Форма: {'Да' if data['uniform'] else 'Нет'}"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_perform_check_confirmation_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Выкладка вечером:", reply_markup=layout_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_layout_evening)
    await callback.answer()


# Обработка выкладки вечером
@router.callback_query(
    F.data.startswith("layout:"), EmployeeStates.waiting_for_layout_evening
)
async def process_layout_evening(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    await state.update_data(layout_evening=val)
    data = await state.get_data()
    required_keys = [
        "trading_point",
        "cleaning",
        "opening_time",
        "layout_afternoon",
        "waste_time",
        "uniform",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_perform_check)
        summary = (
            "Проверьте данные проверки:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Чистота: {data['cleaning']}\n"
            f"Время открытия: {data['opening_time']}\n"
            f"Выкладка днем: {data['layout_afternoon']}\n"
            f"Выкладка вечером: {data['layout_evening']}\n"
            f"Время отходов: {data['waste_time']}\n"
            f"Форма: {'Да' if data['uniform'] else 'Нет'}"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_perform_check_confirmation_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Время отходов:", reply_markup=waste_time_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_waste_time)
    await callback.answer()


# Обработка времени отходов
@router.callback_query(
    F.data.startswith("waste_time:"), EmployeeStates.waiting_for_waste_time
)
async def process_waste_time(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":", 1)[1]
    await state.update_data(waste_time=val)
    data = await state.get_data()
    required_keys = [
        "trading_point",
        "cleaning",
        "opening_time",
        "layout_afternoon",
        "layout_evening",
        "uniform",
    ]
    if all(key in data for key in required_keys):
        await state.set_state(EmployeeStates.confirming_perform_check)
        summary = (
            "Проверьте данные проверки:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Чистота: {data['cleaning']}\n"
            f"Время открытия: {data['opening_time']}\n"
            f"Выкладка днем: {data['layout_afternoon']}\n"
            f"Выкладка вечером: {data['layout_evening']}\n"
            f"Время отходов: {data['waste_time']}\n"
            f"Форма: {'Да' if data['uniform'] else 'Нет'}"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_perform_check_confirmation_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Форма сотрудников в порядке?", reply_markup=yes_no_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_uniform)
    await callback.answer()


# Обработка статуса формы
@router.callback_query(F.data.startswith("yes_no:"), EmployeeStates.waiting_for_uniform)
async def process_uniform(callback: CallbackQuery, state: FSMContext):
    ok = callback.data.split(":", 1)[1] == "Да"
    await state.update_data(uniform=ok)
    data = await state.get_data()
    await state.set_state(EmployeeStates.confirming_perform_check)
    summary = (
        "Проверьте данные проверки:\n"
        f"Торговая точка: {data['trading_point']}\n"
        f"Чистота: {data['cleaning']}\n"
        f"Время открытия: {data['opening_time']}\n"
        f"Выкладка днем: {data['layout_afternoon']}\n"
        f"Выкладка вечером: {data['layout_evening']}\n"
        f"Время отходов: {data['waste_time']}\n"
        f"Форма: {'Да' if data['uniform'] else 'Нет'}"
    )
    await callback.message.edit_text(
        summary, reply_markup=get_perform_check_confirmation_keyboard()
    )
    await callback.answer()


# Обработка подтверждения проверки
@router.callback_query(
    F.data.startswith("confirm_perform_check:"), EmployeeStates.confirming_perform_check
)
async def process_confirm_perform_check(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":", 1)[1]
    data = await state.get_data()
    if action == "yes":
        with SessionLocal() as db:
            emp = get_employee_by_id(db, callback.from_user.id)
            if not emp:
                await callback.message.answer("Сотрудник не найден.")
                await state.clear()
                return
            create_check(
                db,
                employee_id=emp.id,
                trading_point=data["trading_point"],
                cleaning=data["cleaning"],
                opening=data["opening_time"],
                layout_afternoon=data["layout_afternoon"],
                layout_evening=data["layout_evening"],
                waste_time=data["waste_time"],
                uniform=data["uniform"],
            )
            send_to_airtable(
                "perform_check",
                {
                    "employee_id": emp.telegram_id,
                    "trading_point": data["trading_point"],
                    "cleaning": data["cleaning"],
                    "opening_time": data["opening_time"],
                    "layout_afternoon": data["layout_afternoon"],
                    "layout_evening": data["layout_evening"],
                    "waste_time": data["waste_time"],
                    "uniform": data["uniform"],
                },
            )
        await callback.message.edit_text("Проверка завершена.")
        await state.clear()
    elif action == "edit":
        await state.set_state(EmployeeStates.editing_perform_check)
        await callback.message.edit_text(
            "Выберите, что хотите отредактировать:",
            reply_markup=get_perform_check_edit_keyboard(),
        )
    elif action == "cancel":
        await callback.message.edit_text(
            "Процесс проверки отменен.", reply_markup=get_main_menu(callback.message)
        )
        await state.clear()
    await callback.answer()


# Обработка редактирования проверки
@router.callback_query(
    F.data.startswith("edit_perform_check:"), EmployeeStates.editing_perform_check
)
async def process_edit_perform_check(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":", 1)[1]
    if field == "trading_point":
        await callback.message.edit_text(
            "Выберите новую торговую точку:", reply_markup=get_trading_points()
        )
        await state.set_state(EmployeeStates.waiting_for_trading_point_perform_check)
    elif field == "cleaning":
        await callback.message.edit_text(
            "Чистота:", reply_markup=get_cleaning_buttons()
        )
        await state.set_state(EmployeeStates.waiting_for_cleaning)
    elif field == "opening_time":
        await callback.message.edit_text(
            "Введите новое время открытия:", reply_markup=opening_time_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_opening_time)
    elif field == "layout_afternoon":
        await callback.message.edit_text(
            "Выкладка днем:", reply_markup=layout_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_layout_afternoon)
    elif field == "layout_evening":
        await callback.message.edit_text(
            "Выкладка вечером:", reply_markup=layout_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_layout_evening)
    elif field == "waste_time":
        await callback.message.edit_text(
            "Время отходов:", reply_markup=waste_time_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_waste_time)
    elif field == "uniform":
        await callback.message.edit_text(
            "Форма сотрудников в порядке?", reply_markup=yes_no_keyboard()
        )
        await state.set_state(EmployeeStates.waiting_for_uniform)
    elif field == "confirm":
        await state.set_state(EmployeeStates.confirming_perform_check)
        data = await state.get_data()
        summary = (
            "Проверьте данные проверки:\n"
            f"Торговая точка: {data['trading_point']}\n"
            f"Чистота: {data['cleaning']}\n"
            f"Время открытия: {data['opening_time']}\n"
            f"Выкладка днем: {data['layout_afternoon']}\n"
            f"Выкладка вечером: {data['layout_evening']}\n"
            f"Время отходов: {data['waste_time']}\n"
            f"Форма: {'Да' if data['uniform'] else 'Нет'}"
        )
        await callback.message.edit_text(
            summary, reply_markup=get_perform_check_confirmation_keyboard()
        )
    await callback.answer()
