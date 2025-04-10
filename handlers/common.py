from aiogram import F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states.hire_fire import HireFireStates
from keyboards.main import get_main_kb
from aiogram.types import ReplyKeyboardRemove

async def cmd_start(message: Message, state: FSMContext):
    await message.answer(
        "Привет! Выберите действие:",
        reply_markup=get_main_kb()
    )
    await state.set_state(HireFireStates.choosing_action)

async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=ReplyKeyboardRemove()
    )