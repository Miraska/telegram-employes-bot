from aiogram.fsm.state import StatesGroup, State

class AdminStates(StatesGroup):
    choosing_action = State()
    choosing_role = State()
    getting_id = State()
    getting_fio = State()
    firing_id = State()