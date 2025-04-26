from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

__all__ = ["get_admin_menu", "get_roles_menu"]

def get_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Нанять сотрудника", callback_data="admin:Нанять сотрудника")],
        [InlineKeyboardButton(text="Уволить сотрудника", callback_data="admin:Уволить сотрудника")],
    ])

def get_roles_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Обычный сотрудник", callback_data="role:Обычный сотрудник")],
        [InlineKeyboardButton(text="Старший сотрудник", callback_data="role:Старший сотрудник")],
    ])