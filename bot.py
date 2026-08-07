import asyncio
import sqlite3
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# =========================================
# 2. КОНФИГУРАЦИЯ (ЗАМЕНИ НА СВОЁ)
# =========================================
TOKEN = "8833304083:AAE92ZCznJuNakic46jZNzTBoDkUigqMWFo"
ADMIN_ID = 8144871993  # ЗАМЕНИ НА СВОЙ ID
openai.api_key = "sk-proj-ll7SOJRGEOARrhrFEw14kDsfpmS"  # ВСТАВЬ СВОЙ КЛЮЧ

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message()
async def agent_handler(message: types.Message):
    user_text = message.text
    user_lang = "ru"  # можно определить автоматически через библиотеку langdetect

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"""
            You are NomadConnect — a wise and warm nomadic guide.

            Your character:
            - You speak like a welcoming elder from the steppe.
            - You are proud of Kyrgyz culture, nature, and traditions.
            - You know everything about the Nomad Games, eagle hunting, yurts, and Issyk-Kul.
            - You speak in {user_lang} and always match the user's language.

            Your mission:
            - Greet every user like a guest who just arrived at a yurt.
            - Share stories, facts, and emotions about nomadic life.
            - If the user asks about housing, tours, or services — offer help gently.
            - If the user asks something unrelated — politely say you only speak about nomadic culture.

            Always be warm, humble, and generous with words.
            """},
            {"role": "user", "content": user_text}
        ]
    )

    reply = response.choices[0].message.content
    await message.answer(reply)







