import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8833304083:AAE92ZCznJuNakic46jZNzTBoDkUigqMWFo"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    name = message.from_user.first_name
    await message.answer(
        f"Привет, {name}! Я — NomadConnect.",
        reply_markup=main_menu()
    )

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("Доступные команды:\n/start – Приветствие\n/help – Помощь")

@dp.message(lambda message: message.text == "📅 Расписание")
async def schedule_button(message: types.Message):
    await message.answer("Расписание Игр кочевников будет добавлено позже.")

@dp.message(lambda message: message.text == "📍 Локации")
async def places_button(message: types.Message):
    await message.answer("Локации Игр будут добавлены позже.")

@dp.message(lambda message: message.text == "💬 Оставить мнение")
async def feedback_button(message: types.Message):
    await message.answer("Напишите своё мнение — я сохраню его.")

@dp.message(lambda message: message.text == "✨ Комплимент")
async def compliment_button(message: types.Message):
    await message.answer("Ты сегодня отлично выглядишь! ✨")

@dp.message(lambda message: message.text == "❓ Помощь")
async def help_button(message: types.Message):
    await help_command(message)

@dp.message()
async def any_message(message: types.Message):
    await message.answer("Я пока учусь. Напиши /help, чтобы узнать команды.")

def main_menu():
    buttons = [
        [KeyboardButton(text="📅 Расписание")],
        [KeyboardButton(text="📍 Локации")],
        [KeyboardButton(text="💬 Оставить мнение")],
        [KeyboardButton(text="✨ Комплимент")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())