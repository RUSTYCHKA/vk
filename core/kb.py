from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Настройки", callback_data="start=settings")],
        [InlineKeyboardButton(text="Запустить бота", callback_data="start=start")]
    ]
)
settings = InlineKeyboardMarkup(
    inline_keyboard=[
            [InlineKeyboardButton(text="Добавить ТГ каналы", callback_data="add_channels")],
            [InlineKeyboardButton(text="Добавить ВК группу", callback_data="add_vk_group")]
        ])
