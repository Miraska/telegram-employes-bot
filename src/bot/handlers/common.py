from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from bot.states.employee import EmployeeStates
from bot.keyboards.employee import (
    get_trading_points,
    yes_no_keyboard,
    get_cleaning_buttons,
    opening_time_keyboard,
    layout_keyboard,
    waste_time_keyboard,
    add_back_button,
)
from utils.auth import is_admin, is_registered_employee, get_registered_employee

router = Router()

# Функция для создания главного меню
def get_main_menu(message: Message) -> InlineKeyboardMarkup:
    keyboard = []
    if is_admin(message):
        keyboard.append([InlineKeyboardButton(text="Нанять сотрудника", callback_data="admin:hire_employee")])
        keyboard.append([InlineKeyboardButton(text="Уволить сотрудника", callback_data="admin:fire_employee")])
    if is_registered_employee(message.from_user.id):
        emp = get_registered_employee(message.from_user.id)
        if emp.role == "manager":
            keyboard.append([InlineKeyboardButton(text="Начать смену", callback_data="action:start_shift")])
            keyboard.append([InlineKeyboardButton(text="Завершить смену", callback_data="action:end_shift")])
        elif emp.role == "senior_manager":
            keyboard.append([InlineKeyboardButton(text="Выполнить проверку", callback_data="action:perform_check")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Команда /start
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    keyboard = get_main_menu(message)
    if keyboard.inline_keyboard:
        await message.answer("Добро пожаловать! Выберите действие:", reply_markup=keyboard)
    else:
        await message.answer("Добро пожаловать! Ваш ID не добавлен в пул сотрудников, обратитесь к администратору.")

# Команда /cancel
@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    keyboard = get_main_menu(message)
    if keyboard.inline_keyboard:
        await message.answer("Действие отменено. Выберите действие:", reply_markup=keyboard)
    else:
        await message.answer("Действие отменено. Ваш ID не добавлен в пул сотрудников, обратитесь к администратору.")

# Команда /menu
@router.message(Command("menu"))
async def show_menu(message: Message, state: FSMContext):
    keyboard = get_main_menu(message)
    if keyboard.inline_keyboard:
        await message.answer("Ваше меню:", reply_markup=keyboard)
    else:
        await message.answer("У вас нет доступа к меню.")

# Команда /my_id
@router.message(Command("my_id"))
async def get_my_id(message: Message):
    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")

# Обработка кнопки "Назад" для сотрудников
@router.callback_query(F.data == "action:back")
async def back_button_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    state_stack = data.get("state_stack", [])
    
    if state_stack:
        state_stack.pop()
        if state_stack:
            previous_state = state_stack[-1]
            await state.set_state(previous_state)
            await state.update_data(state_stack=state_stack)
            
            if previous_state == EmployeeStates.waiting_for_trading_point:
                new_text = "Выберите торговую точку:"
                new_markup = get_trading_points()
            elif previous_state == EmployeeStates.waiting_for_cash_start:
                new_text = "Введите сумму наличных на начало дня:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_light_on:
                new_text = "Подсветка включена? (Да/Нет)"
                new_markup = add_back_button(yes_no_keyboard())
            elif previous_state == EmployeeStates.waiting_for_camera_on:
                new_text = "Камера подключена? (Да/Нет)"
                new_markup = add_back_button(yes_no_keyboard())
            elif previous_state == EmployeeStates.waiting_for_display_ok:
                new_text = "Выкладка в норме? (Да/Нет)"
                new_markup = add_back_button(yes_no_keyboard())
            elif previous_state == EmployeeStates.waiting_for_wet_cleaning:
                new_text = "Влажная уборка не требуется? (Да/Нет)"
                new_markup = add_back_button(yes_no_keyboard())
            elif previous_state == EmployeeStates.waiting_for_open_comment:
                new_text = "Оставьте комментарий или введите '-' для пропуска:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_photo_start:
                new_text = "Отправьте фото начала смены:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_cash_income:
                new_text = "Введите приход наличных:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_cashless_income:
                new_text = "Введите безналичный доход:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_expenses:
                new_text = "Введите расходы:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_subscriptions:
                new_text = "Введите количество подписок:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_loyalty_cards_issued:
                new_text = "Введите количество выданных карт лояльности:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_incassation:
                new_text = "Введите сумму инкассации:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_qr:
                new_text = "Введите сумму по QR:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_delivery:
                new_text = "Введите сумму доставки:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_online_orders:
                new_text = "Введите количество онлайн-заказов:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_defect:
                new_text = "Введите сумму брака:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_close_comment:
                new_text = "Оставьте комментарий или введите '-' для пропуска:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_photo_end:
                new_text = "Отправьте фото конца смены:"
                new_markup = add_back_button()
            elif previous_state == EmployeeStates.waiting_for_trading_point_perform_check:
                new_text = "Торговая точка:"
                new_markup = get_trading_points()
            elif previous_state == EmployeeStates.waiting_for_cleaning:
                new_text = "Чистота:"
                new_markup = add_back_button(get_cleaning_buttons())
            elif previous_state == EmployeeStates.waiting_for_opening_time:
                new_text = "Введите время открытия:"
                new_markup = add_back_button(opening_time_keyboard())
            elif previous_state == EmployeeStates.waiting_for_layout_afternoon:
                new_text = "Выкладка днем:"
                new_markup = add_back_button(layout_keyboard())
            elif previous_state == EmployeeStates.waiting_for_layout_evening:
                new_text = "Выкладка вечером:"
                new_markup = add_back_button(layout_keyboard())
            elif previous_state == EmployeeStates.waiting_for_waste_time:
                new_text = "Время отходов:"
                new_markup = add_back_button(waste_time_keyboard())
            elif previous_state == EmployeeStates.waiting_for_uniform:
                new_text = "Форма сотрудников в порядке?"
                new_markup = add_back_button(yes_no_keyboard())
            else:
                new_text = "Возврат к предыдущему шагу."
                new_markup = add_back_button()
            
            current_text = callback.message.text
            current_markup = callback.message.reply_markup
            if current_text != new_text or current_markup != new_markup:
                await callback.message.edit_text(new_text, reply_markup=new_markup)
            else:
                await callback.answer("Вы уже на этом шаге.")
        else:
            await state.clear()
            new_text = "Возврат в главное меню."
            new_markup = get_main_menu(callback.message)
            current_text = callback.message.text
            current_markup = callback.message.reply_markup
            if current_text != new_text or current_markup != new_markup:
                await callback.message.edit_text(new_text, reply_markup=new_markup)
            else:
                await callback.answer("Вы уже в главном меню.")
    else:
        await state.clear()
        new_text = "Возврат в главное меню."
        new_markup = get_main_menu(callback.message)
        current_text = callback.message.text
        current_markup = callback.message.reply_markup
        if current_text != new_text or current_markup != new_markup:
            await callback.message.edit_text(new_text, reply_markup=new_markup)
        else:
            await callback.answer("Вы уже в главном меню.")
    await callback.answer()