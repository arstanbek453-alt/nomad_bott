import asyncio
import sqlite3
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ===== КОНФИГУРАЦИЯ =====
TOKEN = "8833304083:AAE92ZCznJuNakic46jZNzTBoDkUigqMWFo"
ADMIN_ID = 8144871993  # ЗАМЕНИ НА СВОЙ ID
openai.api_key = "sk-proj-II7SOJRGEOARrhrFEw14kDsfpmS"  # ВСТАВЬ СВОЙ КЛЮЧ

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== ХРАНИЛИЩА СОСТОЯНИЙ =====
user_state = {}

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS housing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            location TEXT,
            region TEXT,
            capacity INTEGER,
            price INTEGER,
            contact TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_id INTEGER,
            guest_username TEXT,
            host_contact TEXT,
            location TEXT,
            days INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT
        )
    """)
    conn.commit()
    conn.close()

def main_menu():
    buttons = [
        [KeyboardButton(text="🏠 Найти жильё")],
        [KeyboardButton(text="🏠 Сдать жильё")],
        [KeyboardButton(text="🗑️ Удалить объявление")],
        [KeyboardButton(text="📅 Забронировать")],
        [KeyboardButton(text="💬 Оставить мнение")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def region_buttons():
    regions = ["Бишкек", "Ош", "Иссык-Куль (Север)", "Иссык-Куль (Юг)", "Чуй", "Талас", "Джалал-Абад", "Баткен"]
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=r)] for r in regions], resize_keyboard=True)

# ===== СТАРТ =====
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(f"🏔️ Салам, {message.from_user.first_name}! Я — NomadConnect.", reply_markup=main_menu())

# ===== НАЙТИ ЖИЛЬЁ =====
@dp.message(lambda message: message.text == "🏠 Найти жильё")
async def start_search(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"mode": "search", "step": 0}
    await message.answer("📍 Выберите регион:", reply_markup=region_buttons())

# ===== СДАТЬ ЖИЛЬЁ =====
@dp.message(lambda message: message.text == "🏠 Сдать жильё")
async def add_housing_start(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"mode": "add", "step": 0}
    await message.answer("📍 Введите город или локацию:")

# ===== УДАЛИТЬ =====
@dp.message(lambda message: message.text == "🗑️ Удалить объявление")
async def delete_housing_start(message: types.Message):
    await message.answer("Напишите номер объявления для удаления:")

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "delete")
async def delete_housing_confirm(message: types.Message):
    user_id = message.from_user.id
    listing_id = int(message.text)
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM housing WHERE id = ? AND user_id = ?", (listing_id, user_id))
    conn.commit()
    conn.close()
    await message.answer("✅ Объявление удалено.")
    del user_state[user_id]

# ===== БРОНИРОВАНИЕ =====
@dp.message(lambda message: message.text == "📅 Забронировать")
async def start_booking(message: types.Message):
    await message.answer("Введите номер объявления:")

# ===== ОБЩИЙ ОБРАБОТЧИК ДЛЯ КНОПОК =====
@dp.message(lambda message: message.text == "💬 Оставить мнение")
async def feedback_button(message: types.Message):
    await message.answer("📝 Напишите своё мнение.")

@dp.message(lambda message: message.text == "❓ Помощь")
async def help_button(message: types.Message):
    await message.answer("Доступные команды:\n/start – Приветствие\n/help – Помощь")

# ===== АГЕНТ (ОБРАБОТЧИК ВСЕХ ОСТАЛЬНЫХ СООБЩЕНИЙ) =====
@dp.message()
async def agent_handler(message: types.Message):
    user_text = message.text

    # Отправляем запрос ChatGPT, чтобы понять намерение
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": """
            You are an assistant for NomadConnect. Understand user intent:
            - 'search' → user wants to find accommodation
            - 'booking' → user wants to book
            - 'add' → user wants to list property
            - 'delete' → user wants to delete listing
            - 'general' → casual chat or question
            """},
            {"role": "user", "content": user_text}
        ]
    )

    reply = response.choices[0].message.content

    if "search" in reply.lower():
        await start_search(message)
    elif "booking" in reply.lower():
        await start_booking(message)
    elif "add" in reply.lower():
        await add_housing_start(message)
    elif "delete" in reply.lower():
        await delete_housing_start(message)
    else:
        await message.answer(reply)

# ===== ЗАПУСК =====
async def main():
    init_db()
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())








