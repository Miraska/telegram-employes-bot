from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Нанять сотрудника"),
                KeyboardButton(text="Уволить сотрудника"),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_roles_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Обычный менеджер"),
                KeyboardButton(text="Старший менеджер"),
            ],
            [
                KeyboardButton(text="Администратор"),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )