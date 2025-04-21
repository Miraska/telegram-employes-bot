from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_shift_buttons():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отошел"), KeyboardButton(text="Пришел")]
        ],
        resize_keyboard=True
    )

def get_trading_points():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Патриарши")],
            [KeyboardButton(text="Торговая точка 1")],
            [KeyboardButton(text="Торговая точка 2")]
        ],
        resize_keyboard=True
    )

def yes_no_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да"), KeyboardButton(text="Нет")]
        ],
        resize_keyboard=True
    )

def get_cleaning_buttons():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Чисто"), KeyboardButton(text="Требовалась уборка"), KeyboardButton(text="Грязно")]
        ],
        resize_keyboard=True
    )

def opening_time_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Раньше"), KeyboardButton(text="Вовремя"), KeyboardButton(text="Позже")]
        ],
        resize_keyboard=True
    )

def layout_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Правильная выкладка"), KeyboardButton(text="Мелкие исправления"), KeyboardButton(text="Переделка в выкладке")],
        ],
        resize_keyboard=True
    )

def waste_time_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Соблюдено"), KeyboardButton(text="Не соблюдено"), KeyboardButton(text="Фактически не превышено")]
        ],
        resize_keyboard=True
    )