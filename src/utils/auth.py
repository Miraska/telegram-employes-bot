from aiogram.types import Message
from config.settings import settings_config
from database.crud import get_employee_by_id
from database.models import SessionLocal

def is_admin(message: Message) -> bool:
    return message.from_user.username in settings_config.ADMIN_USERNAMES

def is_registered_employee(message: Message) -> bool:
    with SessionLocal() as db:
        employee = get_employee_by_id(db, str(message.from_user.id))
        return employee is not None and employee.is_active