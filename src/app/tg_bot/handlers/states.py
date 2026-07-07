from aiogram.fsm.state import State, StatesGroup

class SearchEventState(StatesGroup):
    setup = State()
    waiting_for_dates = State()