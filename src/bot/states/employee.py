from aiogram.fsm.state import StatesGroup, State

class EmployeeStates(StatesGroup):
    # Существующие состояния для начала смены
    waiting_for_trading_point = State()
    waiting_for_cash_start = State()
    waiting_for_light_on = State()
    waiting_for_camera_on = State()
    waiting_for_display_ok = State()
    waiting_for_wet_cleaning = State()
    waiting_for_open_comment = State()
    waiting_for_photo_start = State()
    confirming_start_shift = State()
    editing_start_shift = State()
    
    # Состояния для закрытия смены
    waiting_for_total_income = State()
    waiting_for_cash_income = State()
    waiting_for_cashless_income = State()
    waiting_for_qr_payments = State()
    waiting_for_returns = State()
    waiting_for_cash_balance = State()
    waiting_for_salary_advance = State()
    waiting_for_incassation_decision = State()
    waiting_for_incassation_amount = State()
    waiting_for_logistics_expenses = State()
    waiting_for_household_expenses = State()
    waiting_for_other_expenses = State()
    waiting_for_online_delivery = State()
    waiting_for_loyalty_cards_issued = State()
    waiting_for_subscriptions = State()
    waiting_for_malfunctions = State()
    waiting_for_requested_products = State()
    waiting_for_photo_end = State()
    confirming_end_shift = State()
    editing_end_shift = State()
    
    # Новое универсальное состояние для редактирования
    editing_field = State()
    
    # Состояния для проверок
    waiting_for_trading_point_perform_check = State()
    waiting_for_cleaning = State()
    waiting_for_opening_time = State()
    waiting_for_layout_afternoon = State()
    waiting_for_layout_evening = State()
    waiting_for_waste_time = State()
    waiting_for_uniform = State()
    confirming_perform_check = State()
    editing_perform_check = State()