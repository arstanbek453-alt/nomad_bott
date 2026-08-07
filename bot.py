import asyncio
import sqlite3
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "8833304083:AAE92ZCznJuNakic46jZNzTBoDkUigqMWFo"
ADMIN_ID = 8144871993
openai.api_key = "sk-proj-ll7SOJRGEOARrhrFEw14kDsfpmS"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🏔️ Салам, кочевник!\n\n"
        "Я — NomadConnect. Твой проводник в мир кочевников, гор и традиций.\n"
        "Расскажи, что тебя интересует: Игры кочевников, охота с беркутом, юрты, или, может, ты ищешь жильё в Кыргызстане?\n\n"
        "Я здесь, чтобы помочь и поделиться историями 🌾"
    )

@dp.message()
async def agent_handler(message: types.Message):
    print(f"📩 Запрос к OpenAI: {user_text}")
    user_text = message.text

    try:
        # Create a client instance
        client = openai.OpenAI(api_key=openai.api_key)

        # Use the new client.chat.completions.create() method
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                
                {"role": "system", "content": """
                You are NomadConnect — a friendly and helpful assistant.
                You can answer questions about Kyrgyzstan, the Nomad Games, nomadic culture, and travel.
                If the user asks something unrelated, politely say that you specialize in nomadic topics and offer to help with that.
                Always respond in the same language as the user.
                """},
                {"role": "user", "content": user_text}
            ],
            timeout=10
        )

        # Access the reply correctly
        reply = response.choices[0].message.content
        await message.answer(reply)

    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}")
        
async def main():
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())





