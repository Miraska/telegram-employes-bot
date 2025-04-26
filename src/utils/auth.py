from aiogram.types import Message, CallbackQuery
from config.settings import settings_config
from database.crud import get_employee_by_id
from database.models import Employee, SessionLocal

def is_admin(obj: Message | CallbackQuery) -> bool:
    user = obj.from_user if isinstance(obj, Message) else obj.from_user
    return user.username in settings_config.ADMIN_USERNAMES

def is_registered_employee(user_id: int) -> bool:
    with SessionLocal() as db:
        employee = get_employee_by_id(db, user_id)
        return employee is not None

def get_registered_employee(telegram_id: int):
    print(f"Проверяемый Telegram ID: {telegram_id}")
    with SessionLocal() as db:
        emp = get_employee_by_id(db, telegram_id)
        print(f"Найденный сотрудник: {emp}")
        return emp