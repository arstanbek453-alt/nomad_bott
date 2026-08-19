import asyncio
import sqlite3
import openai
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# ЗАГРУЗКА КЛЮЧА
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("❌ OPENAI_API_KEY не найден!")

# ===== КОНФИГУРАЦИЯ =====
TOKEN = "8833304083:AAE92ZCznJuNakic46jZNzTBoDkUigqMWFo"
ADMIN_ID = 8144871993

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== БАЗА ЗНАНИЙ ОТЕЛЯ =====
hotel_knowledge = {
    "wi-fi": "🌐 Название сети: Hotel Eden\n🔑 Пароль: Eden2025",
    "завтрак": "🍳 Завтрак подаётся с 7:00 до 10:00 в ресторане на первом этаже",
    "заезд": "🕐 Заезд с 14:00",
    "выезд": "🕐 Выезд до 12:00",
}

# ===== БАЗА ДАННЫХ ДЛЯ ЗАЯВОК =====
def init_db():
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ База данных готова")

# ===== КОМАНДА /START =====
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🏨 Здравствуйте! Я — помощник отеля «Эдем».\n"
        "Я отвечу на ваши вопросы, помогу с бронированием и заявками.\n\n"
        "Например, вы можете спросить:\n"
        "— Какой пароль от Wi-Fi?\n"
        "— Во сколько завтрак?\n"
        "— Есть ли свободные номера?"
    )

# ===== ГЛАВНЫЙ ОБРАБОТЧИК (АГЕНТ) =====
@dp.message()
import asyncio
import sqlite3
import openai
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# ЗАГРУЗКА КЛЮЧА
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("❌ OPENAI_API_KEY не найден!")

# ===== КОНФИГУРАЦИЯ =====
TOKEN = "8833304083:AAE92ZCznJuNakic46jZNzTBoDkUigqMWFo"
ADMIN_ID = 8144871993

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== БАЗА ЗНАНИЙ ОТЕЛЯ =====
hotel_knowledge = {
    "wi-fi": "🌐 Название сети: Hotel Eden\n🔑 Пароль: Eden2025",
    "завтрак": "🍳 Завтрак подаётся с 7:00 до 10:00 в ресторане на первом этаже",
    "заезд": "🕐 Заезд с 14:00",
    "выезд": "🕐 Выезд до 12:00",
}

# ===== БАЗА ДАННЫХ ДЛЯ ЗАЯВОК =====
def init_db():
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ База данных готова")

# ===== КОМАНДА /START =====
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🏨 Здравствуйте! Я — помощник отеля «Эдем».\n"
        "Я отвечу на ваши вопросы, помогу с бронированием и заявками.\n\n"
        "Например, вы можете спросить:\n"
        "— Какой пароль от Wi-Fi?\n"
        "— Во сколько завтрак?\n"
        "— Есть ли свободные номера?"
    )

# ===== ГЛАВНЫЙ ОБРАБОТЧИК (АГЕНТ) =====
@dp.message()
async def agent_handler(message: types.Message):
    user_text = message.text.lower()
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    # 1. Сохраняем запрос в базу данных
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO requests (user_id, username, text) VALUES (?, ?, ?)",
        (user_id, username, user_text)
    )
    conn.commit()
    conn.close()

    # 2. Отправляем уведомление админу
    await bot.send_message(
        ADMIN_ID,
        f"📩 Новый запрос от @{username} (ID: {user_id}):\n\n{user_text}"
    )

    # 3. Проверяем базу знаний
    for key, value in hotel_knowledge.items():
        if key in user_text:
            await message.answer(value)
            return

    # 4. Если не нашли — отправляем в ChatGPT
    thinking = await message.answer("🤔 Ищу ответ...")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
                Ты — помощник отеля «Эдем».
                Отвечай вежливо, кратко и по делу.
                Если не знаешь точного ответа — скажи, что уточнишь и перезвонишь.
                """},
                {"role": "user", "content": user_text}
            ],
            timeout=10
        )

        reply = response.choices[0].message.content
        await thinking.delete()
        await message.answer(reply)

    except Exception as e:
        await thinking.delete()
        await message.answer(f"⚠️ Ошибка: {str(e)}")

# ===== ЗАПУСК =====
async def main():
    init_db()
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


# ===== ЗАПУСК =====
async def main():
    init_db()
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


