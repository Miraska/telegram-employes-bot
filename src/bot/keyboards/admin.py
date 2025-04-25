from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Нанять сотрудника", callback_data="admin:Нанять сотрудника"),
            ],
            [
                InlineKeyboardButton(text="Уволить сотрудника", callback_data="admin:Уволить сотрудника")
            ]
        ]
    )
    return keyboard

def get_roles_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Обычный сотрудник", callback_data="role:Обычный сотрудник")],
            [InlineKeyboardButton(text="Старший сотрудник", callback_data="role:Старший сотрудник")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ]
    )
    return keyboard