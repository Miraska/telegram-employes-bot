from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Нанять сотрудника")],
            [KeyboardButton(text="Уволить сотрудника")]
        ],
        resize_keyboard=True
    )

def get_roles_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Обычный сотрудник")],
            [KeyboardButton(text="Старший сотрудник")]
        ],
        resize_keyboard=True
    )
