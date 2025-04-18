from aiogram.fsm.state import StatesGroup, State

class EmployeeStates(StatesGroup):
    waiting_for_registration = State()
    waiting_for_trading_point = State()
    waiting_for_cash_start = State()

    # Открытие смены – дополнительные поля
    waiting_for_light_on = State()
    waiting_for_camera_on = State()
    waiting_for_display_ok = State()
    waiting_for_wet_cleaning = State()
    waiting_for_open_comment = State()

    waiting_for_photo_start = State()

    waiting_for_cash_income = State()
    waiting_for_cashless_income = State()
    waiting_for_total = State()
    waiting_for_expenses = State()
    waiting_for_balance = State()

    # Закрытие смены – дополнительные поля
    waiting_for_subscriptions = State()
    waiting_for_loyalty_cards_issued = State()
    waiting_for_incassation = State()
    waiting_for_qr = State()
    waiting_for_delivery = State()
    waiting_for_online_orders = State()
    waiting_for_defect = State()
    waiting_for_close_comment = State()

    waiting_for_photo_end = State()
