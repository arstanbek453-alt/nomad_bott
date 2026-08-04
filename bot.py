import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "8833304083:AAE92ZCznJUnAkic46jZNzTBoDkUiqgMWFo"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("✅ Бот работает!")

async def main():
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())
