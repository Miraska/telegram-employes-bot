from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import settings_config

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    trading_point = Column(String)
    is_active = Column(Boolean, default=True)
    hired_at = Column(DateTime, default=datetime.utcnow)
    fired_at = Column(DateTime)

class Shift(Base):
    __tablename__ = 'shifts'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    trading_point = Column(String)
    cash_start = Column(Integer)
    cash_income = Column(Integer)
    cashless_income = Column(Integer)
    total = Column(Integer)
    expenses = Column(String)
    balance = Column(Integer)
    photo_url_start = Column(String)
    photo_url_end = Column(String)
    break_start_at = Column(DateTime)
    total_break_minutes = Column(Integer, default=0)

def init_db():
    engine = create_engine(settings_config.DATABASE_URL)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

SessionLocal = init_db()