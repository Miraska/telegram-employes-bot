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

class Check(Base):
    __tablename__ = 'checks'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    trading_point = Column(String, nullable=False)
    cleaning = Column(String, nullable=False)
    opening = Column(String, nullable=False)
    layout_afternoon = Column(String, nullable=False)
    layout_evening = Column(String, nullable=False)
    waste_time = Column(String, nullable=False)
    uniform = Column(Boolean, default=False)




class Shift(Base):
    __tablename__ = 'shifts'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    trading_point = Column(String)
    cash_start = Column(Integer)
    photo_url_start = Column(String)
    is_light_on = Column(Boolean)
    is_camera_on = Column(Boolean)
    is_display_ok = Column(Boolean)
    is_wet_cleaning_not_required = Column(Boolean)
    open_comment = Column(String)
    break_start_at = Column(DateTime)
    total_break_minutes = Column(Integer, default=0)
    break_message_id = Column(Integer)

    # Поля для закрытия смены
    total_income = Column(Integer)          # Приход всего
    cash_income = Column(Integer)           # Наличные
    cashless_income = Column(Integer)       # Безналичные
    qr_payments = Column(Integer)           # QR-оплаты
    returns = Column(Integer)               # Возвраты
    cash_balance = Column(Integer)          # Остаток наличных в кассе
    salary_advance = Column(Integer)        # В счёт ЗП
    incassation_decision = Column(Boolean)  # Была ли инкассация
    incassation_amount = Column(Integer)    # Сумма инкассации
    logistics_expenses = Column(Integer)    # Расходы: Логистика
    household_expenses = Column(Integer)    # Расходы: Хозяйственные нужды
    other_expenses = Column(Integer)        # Расходы: Иные
    online_delivery = Column(Integer)       # Онлайн-доставка
    loyalty_cards_issued = Column(Integer)  # Выдано карт лояльности
    subscriptions = Column(Integer)         # Подписки
    malfunctions = Column(String)           # Неисправности / поломки
    requested_products = Column(String)     # Необходимый товар
    photo_url_end = Column(String)          # Фото конца смены

def init_db():
    engine = create_engine(settings_config.DATABASE_URL)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

SessionLocal = init_db()
