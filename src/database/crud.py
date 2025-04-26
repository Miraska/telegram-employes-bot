from sqlalchemy.orm import Session
from .models import Employee, Shift, Check
from datetime import datetime

def get_employee_by_id(db: Session, telegram_id: int):
    return db.query(Employee).filter(Employee.telegram_id == int(telegram_id)).first()

def create_check(
    db: Session, 
    employee_id: int, 
    trading_point: str, 
    cleaning: str, 
    opening: str,
    layout_afternoon: str,
    layout_evening: str,
    waste_time: str,
    uniform: bool
):
    check = Check(
        employee_id=employee_id,
        trading_point=trading_point,
        cleaning=cleaning,
        opening=opening,
        layout_afternoon=layout_afternoon,
        layout_evening=layout_evening,
        waste_time=waste_time,
        uniform=uniform,
    )
    db.add(check)
    db.commit()
    db.refresh(check)
    return check

def create_employee(db: Session, telegram_id: str, username: str, full_name: str, role: str, trading_point: str):
    employee = Employee(
        telegram_id=telegram_id, 
        username=username, 
        full_name=full_name, 
        role=role, 
        trading_point=trading_point
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee

def delete_employee(db: Session, telegram_id: str):
    employee = get_employee_by_id(db, telegram_id)
    if employee:
        db.delete(employee)
        db.commit()
        return True
    return False


def fire_employee(db: Session, telegram_id: str):
    employee = get_employee_by_id(db, telegram_id)
    if employee:
        delete_employee(db, telegram_id)
        db.commit()
        return employee
    return None

def create_shift(
    db: Session, 
    employee_id: int, 
    trading_point: str, 
    cash_start: int, 
    photo_url: str,
    is_light_on: bool,
    is_camera_on: bool,
    is_display_ok: bool,
    is_wet_cleaning_not_required: bool,
    open_comment: str
):
    shift = Shift(
        employee_id=employee_id,
        start_time=datetime.utcnow(),
        trading_point=trading_point,
        cash_start=cash_start,
        photo_url_start=photo_url,
        is_light_on=is_light_on,
        is_camera_on=is_camera_on,
        is_display_ok=is_display_ok,
        is_wet_cleaning_not_required=is_wet_cleaning_not_required,
        open_comment=open_comment
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift

def end_shift(
    db: Session, 
    shift_id: int, 
    cash_income: int, 
    cashless_income: int, 
    total: int, 
    expenses: str, 
    balance: int, 
    photo_url: str,
    subscriptions: str,
    loyalty_cards_issued: str,
    incassation: str,
    qr: str,
    delivery: str,
    online_orders: str,
    defect: str,
    close_comment: str
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if shift:
        shift.end_time = datetime.utcnow()
        shift.cash_income = cash_income
        shift.cashless_income = cashless_income
        shift.total = total
        shift.expenses = expenses
        shift.balance = balance
        shift.photo_url_end = photo_url
        shift.subscriptions = subscriptions
        shift.loyalty_cards_issued = loyalty_cards_issued
        shift.incassation = incassation
        shift.qr = qr
        shift.delivery = delivery
        shift.online_orders = online_orders
        shift.defect = defect
        shift.close_comment = close_comment

        db.commit()
        return shift
    return None
