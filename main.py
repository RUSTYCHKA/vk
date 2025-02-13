import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers.start import bot, handlers_router



file_log = logging.FileHandler(f'./logs/LOG_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log')
console_out = logging.StreamHandler()
logging.basicConfig(
level=logging.INFO,
handlers=(file_log, console_out),
format='%(asctime)s - %(levelname)s - %(message)s',
datefmt='%Y-%m-%d %H:%M:%S'
)


async def main() -> None:
    dp = Dispatcher()

    dp.include_routers(handlers_router)
    
    await bot.delete_webhook(True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
