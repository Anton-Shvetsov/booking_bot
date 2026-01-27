from aiogram.fsm.state import StatesGroup, State


class AdminAddSlots(StatesGroup):
    choosing_day = State()
    choosing_slots = State()


class UserRegistration(StatesGroup):
    waiting_for_name = State()