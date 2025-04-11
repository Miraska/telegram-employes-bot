import unittest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message
from bot.handlers.employee import process_cash_start, process_photo_start
from aiogram.fsm.context import FSMContext

class TestEmployeeHandlers(unittest.TestCase):
    def setUp(self):
        self.message = MagicMock(spec=Message)
        self.state = MagicMock(spec=FSMContext)
        self.state.update_data = AsyncMock()
        self.message.answer = AsyncMock()

    def test_process_cash_start_valid(self):
        self.message.text = "1000"
        asyncio.run(process_cash_start(self.message, self.state))
        self.state.update_data.assert_called_with(cash_start=1000)
        self.message.answer.assert_called_with("Отправьте фото начала смены:")

    def test_process_cash_start_invalid(self):
        self.message.text = "invalid"
        asyncio.run(process_cash_start(self.message, self.state))
        self.message.answer.assert_called_with("Введите корректное число.")

    # Для тестирования photo_start нужно мокать БД и Airtable
    # Здесь упрощенный пример
    def test_process_photo_start(self):
        self.message.photo = [MagicMock(file_id="test_file_id")]
        self.message.from_user.id = 123
        asyncio.run(process_photo_start(self.message, self.state))
        self.message.answer.assert_called()

if __name__ == "__main__":
    unittest.main()