from aiogram.fsm.state import State, StatesGroup


class CircleStates(StatesGroup):
    waiting_location = State()
