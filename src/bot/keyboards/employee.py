from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

__all__ = [
    "get_employee_menu",
    "get_senior_manager_menu",
    "get_shift_buttons",
    "get_trading_points",
    "yes_no_keyboard",
    "get_cleaning_buttons",
    "opening_time_keyboard",
    "layout_keyboard",
    "waste_time_keyboard",
    "add_back_button",
]

def get_employee_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать смену", callback_data="action:start_shift")],
        [InlineKeyboardButton(text="Завершить смену", callback_data="action:end_shift")],
    ])

def get_senior_manager_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выполнить проверку", callback_data="action:perform_check")],
    ])

def get_shift_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Отошел", callback_data="shift:Отошел"),
            InlineKeyboardButton(text="Пришел", callback_data="shift:Пришел")
        ],
        [
            InlineKeyboardButton(text="Завершить смену", callback_data="action:end_shift")
        ]
    ])

def get_trading_points() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Патриарши", callback_data="trading_point:Патриарши")],
        [InlineKeyboardButton(text="Гагаринский", callback_data="trading_point:Гагаринский")],
        [InlineKeyboardButton(text="Рио Ленинский", callback_data="trading_point:Рио Ленинский")],
        [InlineKeyboardButton(text="Саларнс", callback_data="trading_point:Саларнс")],
        [InlineKeyboardButton(text="Мега Белая Дача (1)", callback_data="trading_point:Мега Белая Дача (1)")],
        [InlineKeyboardButton(text="Водный", callback_data="trading_point:Водный")],
        [InlineKeyboardButton(text="Вегас Кунцево", callback_data="trading_point:Вегас Кунцево")],
        [InlineKeyboardButton(text="Вегас Крокус", callback_data="trading_point:Вегас Крокус")],
        [InlineKeyboardButton(text="Белая Дача (2)", callback_data="trading_point:Белая Дача (2)")],
        [InlineKeyboardButton(text="Европолис", callback_data="trading_point:Европолис")],
        [InlineKeyboardButton(text="Рио Дмитров", callback_data="trading_point:Рио Дмитров")],
        [InlineKeyboardButton(text="Пушкино Парк", callback_data="trading_point:Пушкино Парк")],
        [InlineKeyboardButton(text="Патрихи", callback_data="trading_point:Патрихи")],
        [InlineKeyboardButton(text="Лефортово", callback_data="trading_point:Лефортово")],
        [InlineKeyboardButton(text="Красный Кнт", callback_data="trading_point:Красный Кнт")],
    ])

def yes_no_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да", callback_data="yes_no:Да"),
            InlineKeyboardButton(text="Нет", callback_data="yes_no:Нет"),
        ]
    ])

def get_cleaning_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Чисто", callback_data="cleaning:Чисто")],
        [InlineKeyboardButton(text="Требовалась уборка", callback_data="cleaning:Требовалась уборка")],
        [InlineKeyboardButton(text="Грязно", callback_data="cleaning:Грязно")],
    ])

def opening_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Раньше", callback_data="opening_time:Раньше")],
        [InlineKeyboardButton(text="Вовремя", callback_data="opening_time:Вовремя")],
        [InlineKeyboardButton(text="Позже", callback_data="opening_time:Позже")],
    ])

def layout_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Правильная выкладка", callback_data="layout:Правильная выкладка")],
        [InlineKeyboardButton(text="Мелкие исправления", callback_data="layout:Мелкие исправления")],
        [InlineKeyboardButton(text="Переделка выкладки", callback_data="layout:Переделка в выкладке")],
    ])

def waste_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Соблюдено", callback_data="waste_time:Соблюдено")],
        [InlineKeyboardButton(text="Не соблюдено", callback_data="waste_time:Не соблюдено")],
        [InlineKeyboardButton(text="Фактически не превышено", callback_data="waste_time:Фактически не превышено")],
    ])

def add_back_button(keyboard: InlineKeyboardMarkup = None) -> InlineKeyboardMarkup:
    back_button = InlineKeyboardButton(text="Назад", callback_data="action:back")
    if keyboard is None:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[back_button]])
    else:
        keyboard.inline_keyboard.append([back_button])
    return keyboard





# Функции для клавиатур подтверждения и редактирования
def get_start_shift_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_start_shift:yes")],
        [InlineKeyboardButton(text="Редактировать", callback_data="confirm_start_shift:edit")],
        [InlineKeyboardButton(text="Отмена", callback_data="confirm_start_shift:cancel")]
    ])

def get_start_shift_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Торговая точка", callback_data="edit_start_shift:trading_point")],
        [InlineKeyboardButton(text="Сумма наличных", callback_data="edit_start_shift:cash_start")],
        [InlineKeyboardButton(text="Подсветка", callback_data="edit_start_shift:is_light_on")],
        [InlineKeyboardButton(text="Камера", callback_data="edit_start_shift:is_camera_on")],
        [InlineKeyboardButton(text="Выкладка", callback_data="edit_start_shift:is_display_ok")],
        [InlineKeyboardButton(text="Влажная уборка", callback_data="edit_start_shift:is_wet_cleaning_not_required")],
        [InlineKeyboardButton(text="Комментарий", callback_data="edit_start_shift:open_comment")],
        [InlineKeyboardButton(text="Фото", callback_data="edit_start_shift:photo_start")],
        [InlineKeyboardButton(text="Подтвердить данные", callback_data="edit_start_shift:confirm")]
    ])

def get_end_shift_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_end_shift:yes")],
        [InlineKeyboardButton(text="Редактировать", callback_data="confirm_end_shift:edit")],
        [InlineKeyboardButton(text="Отмена", callback_data="confirm_end_shift:cancel")]
    ])

def get_end_shift_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Приход наличных", callback_data="edit_end_shift:cash_income")],
        [InlineKeyboardButton(text="Безналичный доход", callback_data="edit_end_shift:cashless_income")],
        [InlineKeyboardButton(text="Расходы", callback_data="edit_end_shift:expenses")],
        [InlineKeyboardButton(text="Подписки", callback_data="edit_end_shift:subscriptions")],
        [InlineKeyboardButton(text="Карты лояльности", callback_data="edit_end_shift:loyalty_cards_issued")],
        [InlineKeyboardButton(text="Инкассация", callback_data="edit_end_shift:incassation")],
        [InlineKeyboardButton(text="QR", callback_data="edit_end_shift:qr")],
        [InlineKeyboardButton(text="Доставка", callback_data="edit_end_shift:delivery")],
        [InlineKeyboardButton(text="Онлайн-заказы", callback_data="edit_end_shift:online_orders")],
        [InlineKeyboardButton(text="Брак", callback_data="edit_end_shift:defect")],
        [InlineKeyboardButton(text="Комментарий", callback_data="edit_end_shift:close_comment")],
        [InlineKeyboardButton(text="Фото", callback_data="edit_end_shift:photo_end")],
        [InlineKeyboardButton(text="Подтвердить данные", callback_data="edit_end_shift:confirm")]
    ])

def get_perform_check_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_perform_check:yes")],
        [InlineKeyboardButton(text="Редактировать", callback_data="confirm_perform_check:edit")],
        [InlineKeyboardButton(text="Отмена", callback_data="confirm_perform_check:cancel")]
    ])

def get_perform_check_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Торговая точка", callback_data="edit_perform_check:trading_point")],
        [InlineKeyboardButton(text="Чистота", callback_data="edit_perform_check:cleaning")],
        [InlineKeyboardButton(text="Время открытия", callback_data="edit_perform_check:opening_time")],
        [InlineKeyboardButton(text="Выкладка днем", callback_data="edit_perform_check:layout_afternoon")],
        [InlineKeyboardButton(text="Выкладка вечером", callback_data="edit_perform_check:layout_evening")],
        [InlineKeyboardButton(text="Время отходов", callback_data="edit_perform_check:waste_time")],
        [InlineKeyboardButton(text="Форма", callback_data="edit_perform_check:uniform")],
        [InlineKeyboardButton(text="Подтвердить данные", callback_data="edit_perform_check:confirm")]
    ])