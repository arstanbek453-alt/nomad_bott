import asyncio
import sqlite3
import random
import openai
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# =========================================
# КОНФИГУРАЦИЯ (ЗАМЕНИ НА СВОЁ)
# =========================================
TOKEN = "8833304083:AAE92ZCznJuNakic46jZNzTBoDkUigqMWFo"
ADMIN_ID = 8144871993  # ЗАМЕНИ НА СВОЙ ID
openai.api_key = os.getenv("OPENAI_API_KEY")


bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== БАЗА ДАННЫХ =====
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
        "🇺🇸 Hello! I'm an AI assistant for your business.\n"
        "I can answer questions, collect inquiries, and help your customers 24/7.\n\n"
        "Just write what you need."
    )

# ===== ГЛАВНЫЙ АГЕНТ =====
@dp.message()
async def agent_handler(message: types.Message):
    user_text = message.text
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    # Сохраняем запрос в базу
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO requests (user_id, username, text) VALUES (?, ?, ?)",
        (user_id, username, user_text)
    )
    conn.commit()
    conn.close()

    # Отправляем уведомление администратору
    await bot.send_message(
        ADMIN_ID,
        f"📩 New inquiry from @{username} (ID: {user_id}):\n\n{user_text}"
    )

    # Ответ через ChatGPT
    thinking = await message.answer("🤔 Thinking...")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
                You are a professional AI assistant for small businesses in the USA.
                Your job is to help customers, answer questions, and collect inquiries.

                Be polite, fast, and helpful.
                Always respond in English.
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
        await message.answer(f"⚠️ Error: {str(e)}")

# ===== ЗАПУСК =====
async def main():
    init_db()
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



