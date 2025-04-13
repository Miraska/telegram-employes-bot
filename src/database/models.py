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

    # Дополнительные поля для открытия смены (скрин с зелеными галочками)
    is_light_on = Column(Boolean, default=False)               # Подсветка включена
    is_camera_on = Column(Boolean, default=False)              # Камера подключена
    is_display_ok = Column(Boolean, default=False)             # Выкладка в норме
    is_wet_cleaning_not_required = Column(Boolean, default=False)  # Влажная уборка не требуется
    open_comment = Column(String)                              # Комментарий при открытии

    # Дополнительные поля для закрытия смены
    subscriptions = Column(String)      # Подписки
    loyalty_cards_issued = Column(String)  # Выдано карт лояльности
    incassation = Column(String)          # Инкассация
    qr = Column(String)                   # QR
    delivery = Column(String)             # Доставка
    online_orders = Column(String)        # Онлайн заказы
    defect = Column(String)               # Брак
    close_comment = Column(String)        # Комментарий при закрытии

def init_db():
    engine = create_engine(settings_config.DATABASE_URL)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

SessionLocal = init_db()
