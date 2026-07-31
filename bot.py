import asyncio
import os
import csv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8833304083:AAE92ZCznJuNakic46jZNzTBoDkUigqMWFo"

ADMIN_ID =  8144871993

bot = Bot(token=TOKEN)
dp = Dispatcher()
user_language = {}

async def save_order(user_id, username, service, amount, bot):
    file_exists = os.path.isfile("orders.csv")
    with open("orders.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["user_id", "username", "service", "amount", "status"])
        writer.writerow([user_id, username, service, amount, "pending"])

    # Уведомление администратору
    await bot.send_message(
        ADMIN_ID,
        f"🆕 Новый заказ!\n\n"
        f"👤 Пользователь: @{username}\n"
        f"📦 Услуга: {service}\n"
        f"💰 Сумма: {amount} сом\n"
        f"🆔 ID: {user_id}"
    )

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

@dp.message(Command("getfeedback"))
async def get_feedback(message: types.Message):
    try:
        with open("feedback.txt", "r", encoding="utf-8") as f:
            feedbacks = f.read()
        if feedbacks.strip():
            await message.answer(f"📋 Сохранённые мнения:\n\n{feedbacks}")
        else:
            await message.answer("📭 Пока нет мнений.")
    except FileNotFoundError:
        await message.answer("📭 Файл с мнениями пока не создан.")

@dp.message(Command("schedule"))
async def schedule_command(message: types.Message):
    text = (
        "📅 *Расписание Игр кочевников 2026*\n\n"
        "🏔️ 31 августа — Открытие в Бишкеке\n"
        "🚌 1 сентября — Переезд на Иссык-Куль\n"
        "🏹 2–6 сентября — Основные соревнования\n"
        "🎭 6 сентября — Закрытие в Чолпон-Ате\n\n"
        "Подробное расписание будет добавляться по мере уточнения."
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("places"))
async def places_command(message: types.Message):
    text = (
        "📍 *Главные локации Игр кочевников 2026*\n\n"
        "🏔️ *Кырчын* — этногородок, главная площадка\n"
        "🏟️ *Бишкек-Арена* — открытие 31 августа\n"
        "🏞️ *Чолпон-Ата* — соревнования и закрытие\n"
        "🎶 *Рух-Ордо* — культурная программа\n\n"
        "Подробнее о каждой локации — в следующих обновлениях."
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("lang"))
async def choose_language(message: types.Message):
    buttons = [
        [KeyboardButton(text="🇷🇺 Русский")],
        [KeyboardButton(text="🇬🇧 English")],
        [KeyboardButton(text="🇰🇬 Кыргызча")]
    ]
    markup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer("Выберите язык / Тилди тандаңыз / Choose language:", reply_markup=markup)


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

@dp.message(lambda message: message.text == "💬 Оставить мнение")
async def feedback_button(message: types.Message):
    await message.answer("Напишите своё мнение — я сохраню его.")

@dp.message(lambda message: message.text == "🛒 Купить жильё")
async def buy_housing(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    await save_order(user_id, username, "Жильё", 5000, bot)
    await message.answer("✅ Ваш заказ сохранён. Скоро мы свяжемся с вами.")

@dp.message()
async def save_feedback(message: types.Message):
    with open("feedback.txt", "a", encoding="utf-8") as f:
        f.write(message.text + "\n")
    await message.answer("Спасибо! Ваше мнение сохранено.")

@dp.message(lambda message: message.text in ["🇷🇺 Русский", "🇬🇧 English", "🇰🇬 Кыргызча"])
async def set_language(message: types.Message):
    lang = {
        "🇷🇺 Русский": "ru",
        "🇬🇧 English": "en",
        "🇰🇬 Кыргызча": "kg"
    }.get(message.text, "ru")
    user_language[message.from_user.id] = lang
    await message.answer(f"✅ Язык выбран: {message.text}")


@dp.message()
async def any_message(message: types.Message):
    await message.answer("Я пока учусь. Напиши /help, чтобы узнать команды.")

def main_menu():
    buttons = [
        [KeyboardButton(text="📅 Расписание")],
        [KeyboardButton(text="📍 Локации")],
        [KeyboardButton(text="💬 Оставить мнение")],
        [KeyboardButton(text="✨ Комплимент")],
        [KeyboardButton(text="🛒 Купить жильё")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

async def main():
    print(f"👤 Администратор: {ADMIN_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())