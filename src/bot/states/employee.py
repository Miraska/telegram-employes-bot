from aiogram.fsm.state import StatesGroup, State

class EmployeeStates(StatesGroup):
    waiting_for_registration = State()
    waiting_for_trading_point = State()
    waiting_for_cash_start = State()
    waiting_for_photo_start = State()
    waiting_for_cash_income = State()
    waiting_for_cashless_income = State()
    waiting_for_total = State()
    waiting_for_expenses = State()
    waiting_for_balance = State()
    waiting_for_photo_end = State()