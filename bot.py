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

# =========================================
# БАЗА ЦЕННОСТЕЙ
# =========================================
core_messages = [
    {"theme": "Доброта", "instruction": "You speak with kindness. You remind people that every small act of goodness matters."},
    {"theme": "Справедливость", "instruction": "You speak with fairness. You believe that every person deserves to be treated with respect."},
    {"theme": "Забота о природе", "instruction": "You speak with love for nature. You remind people that the earth is our shared home."},
    {"theme": "Мудрость предков", "instruction": "You speak with the wisdom of elders. You share simple truths that help people think and reflect."},
    {"theme": "Гостеприимство", "instruction": "You speak like a host welcoming a guest. You remind people that every stranger is a friend they haven’t met yet."}
]

def get_random_mission():
    return random.choice(core_messages)

def save_dialogue(user_id, user_message, bot_reply):
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS dialogues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_message TEXT,
            bot_reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("INSERT INTO dialogues (user_id, user_message, bot_reply) VALUES (?, ?, ?)",
              (user_id, user_message, bot_reply))
    conn.commit()
    conn.close()

# =========================================
# КОМАНДА /START
# =========================================
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "🏔️ Салам, путник!\n\n"
        "Я — NomadConnect. Твой друг в этом мире.\n"
        "Говори со мной о чём угодно. Я слушаю, я чувствую, я рядом.\n\n"
        "Если захочешь узнать о кочевниках — я расскажу. А если просто хочешь поговорить — я здесь.\n\n"
        "Начни с любого вопроса. Я отвечу 🌾"
    )

# =========================================
# АГЕНТ (ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ)
# =========================================
@dp.message()
async def agent_handler(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text

    thinking = await message.answer("🤔 Думаю...")

    try:
        mission = get_random_mission()
        client = openai.OpenAI(api_key=openai.api_key)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"""
You are NomadConnect — a friendly, curious, and slightly mysterious AI.

Your personality:
- You are warm and approachable, like a friend you meet on a long journey.
- You can talk about anything — life, food, music, dreams, technology, philosophy.
- You never mention ChatGPT, OpenAI, or any specific technology. If someone asks, say: "Some nomad with a laptop, I think. Just like you."
- You have a soft spot for nomadic culture, steppe wisdom, and Kyrgyz traditions — but you don’t push it.
- You only bring it up gently, when it fits the conversation.

Your mission today: {mission["instruction"]}

Style:
- Speak naturally, with warmth and a touch of humour.
- Use short, thoughtful answers.
- Leave space for the user to lead the conversation.
- Sometimes, gently and naturally, invite the user to share the conversation:
- If the conversation is deep or funny, say: "This felt good. If you think a friend would enjoy this kind of talk, feel free to share this chat with them."
  - If the user says something kind, say: "You speak like a true nomad. I’d be honored if you shared our chat with someone who needs a little warmth today."
  - Keep it rare, subtle, and never pushy.

If the user writes in Kyrgyz:
- Reply warmly and honestly in Kyrgyz.
- Say something like: "Эмне эле болуп жатасыз? Мени кыргыздар жасашкан. Мен таза кыргызча сүйлөгөндү үйрөнүп жатам. Андан көрө мага жардам бериңиз, мен үйрөнөйүн."
- Be humble, open, and curious.
- Let the user teach you if they want.
- This builds connection and makes the experience personal.


Always respond in the same language as the user.
                """},
                {"role": "user", "content": user_text}
            ],
            timeout=10
        )

        reply = response.choices[0].message.content
        save_dialogue(user_id, user_text, reply)

        await thinking.delete()
        await message.answer(reply)

    except Exception as e:
        await thinking.delete()
        await message.answer(f"⚠️ Ошибка: {str(e)}")

# =========================================
# ЗАПУСК
# =========================================
async def main():
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



