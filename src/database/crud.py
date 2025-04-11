from sqlalchemy.orm import Session
from .models import Employee, Shift
from datetime import datetime

def get_employee_by_id(db: Session, telegram_id: str):
    return db.query(Employee).filter(Employee.telegram_id == telegram_id).first()

def create_employee(db: Session, telegram_id: str, username: str, full_name: str, role: str, trading_point: str):
    employee = Employee(telegram_id=telegram_id, username=username, full_name=full_name, role=role, trading_point=trading_point)
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee

def fire_employee(db: Session, telegram_id: str):
    employee = get_employee_by_id(db, telegram_id)
    if employee:
        employee.is_active = False
        employee.fired_at = datetime.utcnow()
        db.commit()
        return employee
    return None

def create_shift(db: Session, employee_id: int, trading_point: str, cash_start: int, photo_url: str):
    shift = Shift(employee_id=employee_id, start_time=datetime.utcnow(), trading_point=trading_point, cash_start=cash_start, photo_url_start=photo_url)
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift

def end_shift(db: Session, shift_id: int, cash_income: int, cashless_income: int, total: int, expenses: str, balance: int, photo_url: str):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if shift:
        shift.end_time = datetime.utcnow()
        shift.cash_income = cash_income
        shift.cashless_income = cashless_income
        shift.total = total
        shift.expenses = expenses
        shift.balance = balance
        shift.photo_url_end = photo_url
        db.commit()
        return shift
    return None