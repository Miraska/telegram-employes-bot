from sqlalchemy.orm import Session
from .models import Employee
from datetime import datetime

def get_employee_by_id(db: Session, employee_id: str):
    return db.query(Employee).filter(
        (Employee.telegram_id == employee_id) | 
        (Employee.username == employee_id)
    ).first()

def create_employee(db: Session, telegram_id: str, username: str, full_name: str, role: str):
    db_employee = Employee(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        role=role
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def fire_employee(db: Session, employee_id: str):
    employee = get_employee_by_id(db, employee_id)
    if employee:
        employee.is_active = False
        employee.fired_at = datetime.utcnow()
        db.commit()
        return employee
    return None

def get_active_employees(db: Session):
    return db.query(Employee).filter(Employee.is_active == True).all()