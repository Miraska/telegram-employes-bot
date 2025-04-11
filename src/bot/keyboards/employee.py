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
