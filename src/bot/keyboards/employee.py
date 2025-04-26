from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

__all__ = [
    "get_employee_menu",
    "get_senior_manager_menu",
    "get_shift_buttons",
    "get_trading_points",
    "yes_no_keyboard",
    "get_cleaning_buttons",
    "opening_time_keyboard",
    "layout_keyboard",
    "waste_time_keyboard",
]

def get_employee_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать смену", callback_data="action:start_shift")],
        [InlineKeyboardButton(text="Завершить смену", callback_data="action:end_shift")],
    ])

def get_senior_manager_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выполнить проверку", callback_data="action:perform_check")],
    ])

def get_shift_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Отошел", callback_data="shift:Отошел"),
            InlineKeyboardButton(text="Пришел", callback_data="shift:Пришел"),
        ]
    ])

def get_trading_points() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Патриарши", callback_data="trading_point:Патриарши")],
        [InlineKeyboardButton(text="Торговая точка 1", callback_data="trading_point:Торговая точка 1")],
        [InlineKeyboardButton(text="Торговая точка 2", callback_data="trading_point:Торговая точка 2")],
    ])

def yes_no_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да", callback_data="yes_no:Да"),
            InlineKeyboardButton(text="Нет", callback_data="yes_no:Нет"),
        ]
    ])

def get_cleaning_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Чисто", callback_data="cleaning:Чисто")],
        [InlineKeyboardButton(text="Требовалась уборка", callback_data="cleaning:Требовалась уборка")],
        [InlineKeyboardButton(text="Грязно", callback_data="cleaning:Грязно")],
    ])

def opening_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Раньше", callback_data="opening_time:Раньше")],
        [InlineKeyboardButton(text="Вовремя", callback_data="opening_time:Вовремя")],
        [InlineKeyboardButton(text="Позже", callback_data="opening_time:Позже")],
    ])

def layout_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Правильная выкладка", callback_data="layout:Правильная выкладка")],
        [InlineKeyboardButton(text="Мелкие исправления", callback_data="layout:Мелкие исправления")],
        [InlineKeyboardButton(text="Переделка в выкладке", callback_data="layout:Переделка в выкладке")],
    ])

def waste_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Соблюдено", callback_data="waste_time:Соблюдено")],
        [InlineKeyboardButton(text="Не соблюдено", callback_data="waste_time:Не соблюдено")],
        [InlineKeyboardButton(text="Фактически не превышено", callback_data="waste_time:Фактически не превышено")],
    ])