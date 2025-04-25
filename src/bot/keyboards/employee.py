from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_shift_buttons():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Отошел", callback_data="shift:Отошел"),
                InlineKeyboardButton(text="Пришел", callback_data="shift:Пришел")
            ]
        ]
    )
    return keyboard

def get_trading_points():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Патриарши", callback_data="trading_point:Патриарши")],
            [InlineKeyboardButton(text="Торговая точка 1", callback_data="trading_point:Торговая точка 1")],
            [InlineKeyboardButton(text="Торговая точка 2", callback_data="trading_point:Торговая точка 2")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
    )
    return keyboard

def yes_no_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="yes_no:Да"),
                InlineKeyboardButton(text="Нет", callback_data="yes_no:Нет")
            ],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
    )
    return keyboard

def get_cleaning_buttons():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Чисто", callback_data="cleaning:Чисто")],
            [InlineKeyboardButton(text="Требовалась уборка", callback_data="cleaning:Требовалась уборка")],
            [InlineKeyboardButton(text="Грязно", callback_data="cleaning:Грязно")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
    )
    return keyboard

def opening_time_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Раньше", callback_data="opening_time:Раньше")],
            [InlineKeyboardButton(text="Вовремя", callback_data="opening_time:Вовремя")],
            [InlineKeyboardButton(text="Позже", callback_data="opening_time:Позже")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
    )
    return keyboard

def layout_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Правильная выкладка", callback_data="layout:Правильная выкладка")],
            [InlineKeyboardButton(text="Мелкие исправления", callback_data="layout:Мелкие исправления")],
            [InlineKeyboardButton(text="Переделка в выкладке", callback_data="layout:Переделка в выкладке")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
    )
    return keyboard

def waste_time_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Соблюдено", callback_data="waste_time:Соблюдено")],
            [InlineKeyboardButton(text="Не соблюдено", callback_data="waste_time:Не соблюдено")],
            [InlineKeyboardButton(text="Фактически не превышено", callback_data="waste_time:Фактически не превышено")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
    )
    return keyboard

def get_employee_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Начать смену", callback_data="action:start_shift")],
            [InlineKeyboardButton(text="Завершить смену", callback_data="action:end_shift")]
        ]
    )
    return keyboard

def get_senior_manager_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Выполнить проверку", callback_data="action:perform_check")]
        ]
    )
    return keyboard