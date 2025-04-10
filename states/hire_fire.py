from aiogram.fsm.state import State, StatesGroup

class HireFireStates(StatesGroup):
    choosing_action = State()
    choosing_role = State()
    get_tg_id = State()
    get_fio = State()
    get_fire_id = State()