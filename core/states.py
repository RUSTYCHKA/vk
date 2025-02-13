from aiogram.fsm.state import StatesGroup, State


class States(StatesGroup):
    vk_group = State()
    tg_channels = State()