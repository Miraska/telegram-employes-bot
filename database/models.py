from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import settings


Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    hired_at = Column(DateTime, default=datetime.utcnow)
    fired_at = Column(DateTime)
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.full_name}', role='{self.role}')>"

def init_db():
    engine = create_engine(f'sqlite:///{settings.DATABASE_NAME}')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

SessionLocal = init_db()