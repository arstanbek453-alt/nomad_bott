import asyncio
import csv
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8833304083:AAE92ZCznJuNakic46jZNzTBoDkUigqMWFo"
ADMIN_ID = 8144871993 

def init_db():
    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()

    # --- ТАБЛИЦЫ, КОТОРЫЕ УЖЕ БЫЛИ ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            language TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT,
            amount INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- НОВЫЕ ТАБЛИЦЫ ДЛЯ ГОЛОСОВАНИЯ ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            user_id INTEGER,
            candidate_id INTEGER,
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            PRIMARY KEY (user_id, candidate_id)
        )
    """)

    # --- ДОБАВЛЯЕМ СТРАНЫ (ТОЛЬКО ЕСЛИ ИХ ЕЩЁ НЕТ) ---
    countries = ["🇰🇬 Кыргызстан", "🇰🇿 Казахстан", "🇹🇷 Турция", "🇲🇳 Монголия", "🇺🇿 Узбекистан"]
    for country in countries:
        cursor.execute("INSERT OR IGNORE INTO candidates (name) VALUES (?)", (country,))

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_language = {}

def main_menu():
    buttons = [
        [KeyboardButton(text="📅 Расписание")],
        [KeyboardButton(text="📍 Локации")],
        [KeyboardButton(text="💬 Оставить мнение")],
        [KeyboardButton(text="✨ Комплимент")],
        [KeyboardButton(text="🛒 Купить жильё")],
        [KeyboardButton(text="🍶 Кымыз")],          # ← новая кнопка
        [KeyboardButton(text="📤 Поделиться")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

async def save_order(user_id, username, service, amount, bot):
    file_exists = os.path.isfile("orders.csv")
    with open("orders.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["user_id", "username", "service", "amount", "status"])
        writer.writerow([user_id, username, service, amount, "pending"])
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
    user_id = message.from_user.id
    lang = user_language.get(user_id, "ru")
    name = message.from_user.first_name
    if lang == "kg":
        text = f"🏔️ Салам, {name}! Мен — NomadConnect. Сизди көргөнүмө кубанычтуумун!"
    elif lang == "en":
        text = f"🏔️ Hello, {name}! I'm NomadConnect. Nice to see you!"
    else:
        text = f"🏔️ Привет, {name}! Я — NomadConnect. Рад тебя видеть!"
    await message.answer(text, reply_markup=main_menu())

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("Доступные команды:\n/start – Приветствие\n/help – Помощь\n/lang – Выбор языка")

@dp.message(Command("lang"))
async def choose_language(message: types.Message):
    buttons = [
        [KeyboardButton(text="🇷🇺 Русский")],
        [KeyboardButton(text="🇬🇧 English")],
        [KeyboardButton(text="🇰🇬 Кыргызча")]
    ]
    markup = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    await message.answer("Выберите язык / Тилди тандаңыз / Choose language:", reply_markup=markup)

@dp.message(lambda message: message.text in ["🇷🇺 Русский", "🇬🇧 English", "🇰🇬 Кыргызча"])
async def set_language(message: types.Message):
    lang = {
        "🇷🇺 Русский": "ru",
        "🇬🇧 English": "en",
        "🇰🇬 Кыргызча": "kg"
    }.get(message.text, "ru")
    user_language[message.from_user.id] = lang
    await message.answer(f"✅ Язык выбран: {message.text}")

@dp.message(Command("schedule"))
async def schedule_command(message: types.Message):
    text = (
        "📅 *Расписание Игр кочевников 2026*\n\n"
        "🏔️ 31 августа — Открытие в Бишкеке\n"
        "🚌 1 сентября — Переезд на Иссык-Куль\n"
        "🏹 2–6 сентября — Основные соревнования\n"
        "🎭 6 сентября — Закрытие в Чолпон-Ате"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("places"))
async def places_command(message: types.Message):
    text = (
        "📍 *Главные локации Игр кочевников 2026*\n\n"
        "🏔️ *Кырчын* — этногородок\n"
        "🏟️ *Бишкек-Арена* — открытие\n"
        "🏞️ *Чолпон-Ата* — соревнования\n"
        "🎶 *Рух-Ордо* — культура"
    )
    await message.answer(text, parse_mode="Markdown")

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

@dp.message(lambda message: message.text == "📤 Поделиться")
async def share_bot(message: types.Message):
    await message.answer(
        "📤 Поделитесь ботом с друзьями!\n\n"
        "Отправьте им ссылку:\n"
        "https://t.me/NomadConnect_OfficialBot"
    )

@dp.message(lambda message: message.text == "📅 Расписание")
async def schedule_button(message: types.Message):
    await schedule_command(message)

@dp.message(lambda message: message.text == "📍 Локации")
async def places_button(message: types.Message):
    await places_command(message)

@dp.message(lambda message: message.text == "💬 Оставить мнение")
async def feedback_button(message: types.Message):
    await message.answer("📝 Напишите своё мнение — я сохраню его.")

@dp.message(lambda message: message.text == "✨ Комплимент")
async def compliment_button(message: types.Message):
    await message.answer("✨ Ты сегодня отлично выглядишь!")

@dp.message(lambda message: message.text == "🛒 Купить жильё")
async def buy_housing(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    await save_order(user_id, username, "Жильё", 5000, bot)
    await message.answer("✅ Ваш заказ сохранён. Скоро мы свяжемся с вами.")

@dp.message(lambda message: message.text == "🍶 Кымыз")
async def kymyz_order(message: types.Message):
    await message.answer(
        "🍶 *Кымыз — напиток кочевников*\n\n"
        "Полезный, освежающий, с тысячелетней историей.\n\n"
        "Выберите объём:\n"
        "1️⃣ 1 литр — 300 сом\n"
        "2️⃣ 3 литра — 800 сом\n"
        "3️⃣ 5 литров — 1200 сом\n\n"
        "Напишите номер (1, 2 или 3), чтобы оформить заказ."
    )

@dp.message(lambda message: message.text in ["1", "2", "3"])
async def kymyz_amount(message: types.Message):
    amounts = {
        "1": ("1 литр", 300),
        "2": ("3 литра", 800),
        "3": ("5 литров", 1200)
    }
    service, price = amounts[message.text]
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    await save_order(user_id, username, f"Кымыз ({service})", price, bot)
    await message.answer(f"✅ Заказ на {service} кымыза оформлен!\nСумма: {price} сом.\nСкоро мы свяжемся с вами.")

@dp.message(lambda message: message.text == "❓ Помощь")
async def help_button(message: types.Message):
    await help_command(message)

@dp.message()
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_language and message.text not in ["🇷🇺 Русский", "🇬🇧 English", "🇰🇬 Кыргызча"]:
        await message.answer("Я пока учусь. Напиши /help, чтобы узнать команды.")
    else:
        await message.answer("Я пока учусь. Напиши /help, чтобы узнать команды.")

async def main():
    init_db()
    print("👤 Администратор:", ADMIN_ID)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
