import asyncio
import csv
import os
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

print("🚀 Бот запускается...")
print(f"🔑 Токен: {TOKEN[:10]}...")

TOKEN = "8833304083:AAE92ZCznJUnAkic46jZNzTBoDkUiqgMWFo"
ADMIN_ID = 8144871993  # Замени на свой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_language = {}
housing_data = {}
booking_data = {}
search_data = {}
delete_data = {}

def init_db():
    conn = sqlite3.connect("/data/nomad_bot_new.db")
    cursor = conn.cursor()
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS housing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            location TEXT,
            region TEXT,
            capacity INTEGER,
            price INTEGER,
            contact TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_id INTEGER,
            guest_username TEXT,
            host_contact TEXT,
            location TEXT,
            days INTEGER,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    countries = ["🇰🇬 Кыргызстан", "🇰🇿 Казахстан", "🇹🇷 Турция", "🇲🇳 Монголия", "🇺🇿 Узбекистан"]
    for country in countries:
        cursor.execute("INSERT OR IGNORE INTO candidates (name) VALUES (?)", (country,))
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

def main_menu():
    buttons = [
        [KeyboardButton(text="🏠 Найти жильё")],
        [KeyboardButton(text="🏠 Сдать жильё")],
        [KeyboardButton(text="🗑️ Удалить объявление")],
        [KeyboardButton(text="📅 Забронировать")],
        [KeyboardButton(text="🗳 Голосование")],
        [KeyboardButton(text="📊 Результаты")],
        [KeyboardButton(text="💬 Оставить мнение")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def region_buttons():
    buttons = [
        [KeyboardButton(text="🏙️ Бишкек")],
        [KeyboardButton(text="🏙️ Ош")],
        [KeyboardButton(text="🏞️ Иссык-Куль (Север)")],
        [KeyboardButton(text="🏞️ Иссык-Куль (Юг)")],
        [KeyboardButton(text="🌾 Чуй")],
        [KeyboardButton(text="🌿 Талас")],
        [KeyboardButton(text="🌄 Джалал-Абад")],
        [KeyboardButton(text="🏜️ Баткен")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    conn = sqlite3.connect("/data/nomad_bot_new.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()
    name = message.from_user.first_name
    await message.answer(f"🏔️ Салам, {name}! Я — NomadConnect. Рад тебя видеть!", reply_markup=main_menu())

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("Доступные команды:\n/start – Приветствие\n/help – Помощь\n/vote – Голосование\n/results – Результаты")

@dp.message(Command("vote"))
async def vote_command(message: types.Message):
    conn = sqlite3.connect("/data/nomad_bot_new.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM votes WHERE user_id = ?", (message.from_user.id,))
    count = cursor.fetchone()[0]
    if count > 0:
        await message.answer("✅ Вы уже проголосовали.")
        conn.close()
        return
    cursor.execute("SELECT id, name FROM candidates")
    candidates = cursor.fetchall()
    conn.close()
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"vote_{id}")] for id, name in candidates]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("🗳 Выберите страну:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("vote_"))
async def process_vote(callback: types.CallbackQuery):
    candidate_id = int(callback.data.split("_")[1])
    conn = sqlite3.connect("/data/nomad_bot_new.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM votes WHERE user_id = ?", (callback.from_user.id,))
    count = cursor.fetchone()[0]
    if count > 0:
        await callback.answer("Вы уже голосовали!", show_alert=True)
        conn.close()
        return
    cursor.execute("INSERT INTO votes (user_id, candidate_id) VALUES (?, ?)", (callback.from_user.id, candidate_id))
    conn.commit()
    conn.close()
    await callback.answer("✅ Ваш голос учтён!", show_alert=True)
    await callback.message.edit_text("🗳 Спасибо за участие!")

@dp.message(Command("results"))
async def results_command(message: types.Message):
    conn = sqlite3.connect("/data/nomad_bot_new.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.name, COUNT(v.candidate_id) as votes
        FROM candidates c
        LEFT JOIN votes v ON c.id = v.candidate_id
        GROUP BY c.id
        ORDER BY votes DESC
    """)
    results = cursor.fetchall()
    conn.close()
    if not results or all(r[1] == 0 for r in results):
        await message.answer("📭 Пока нет голосов. Напишите /vote")
        return
    text = "📊 *Результаты голосования:*\n\n"
    for name, count in results:
        text += f"{name}: {count} голосов\n"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("getfeedback"))
async def get_feedback(message: types.Message):
    try:
        with open("/data/feedback.txt", "r", encoding="utf-8") as f:
            data = f.read()
        if data.strip():
            await message.answer(f"📋 Сохранённые мнения:\n\n{data}")
        else:
            await message.answer("📭 Пока нет мнений.")
    except FileNotFoundError:
        await message.answer("📭 Файл с мнениями пока не создан.")

# ---- ЖИЛЬЁ: НАЙТИ ----
@dp.message(lambda message: message.text == "🏠 Найти жильё")
async def start_search(message: types.Message):
    user_id = message.from_user.id
    search_data[user_id] = {"step": "region"}
    await message.answer("📍 Выберите регион:", reply_markup=region_buttons())

@dp.message(lambda message: message.text in [
    "🏙️ Бишкек", "🏙️ Ош", "🏞️ Иссык-Куль (Север)", "🏞️ Иссык-Куль (Юг)",

    "🌾 Чуй", "🌿 Талас", "🌄 Джалал-Абад", "🏜️ Баткен"
] and message.from_user.id in search_data)
async def search_region(message: types.Message):
    user_id = message.from_user.id
    search_data[user_id]["region"] = message.text
    search_data[user_id]["step"] = "capacity"
    await message.answer("👥 Сколько человек должно поместиться?", reply_markup=ReplyKeyboardRemove())

@dp.message(lambda message: message.text.isdigit() and message.from_user.id in search_data and search_data[message.from_user.id].get("step") == "capacity")
async def search_capacity(message: types.Message):
    user_id = message.from_user.id
    search_data[user_id]["capacity"] = int(message.text)
    search_data[user_id]["step"] = "price"
    await message.answer("💰 Максимальная цена за ночь (в сомах):")

@dp.message(lambda message: message.text.isdigit() and message.from_user.id in search_data and search_data[message.from_user.id].get("step") == "price")
async def search_price(message: types.Message):
    user_id = message.from_user.id
    search_data[user_id]["price"] = int(message.text)
    region = search_data[user_id]["region"]
    capacity = search_data[user_id]["capacity"]
    price = search_data[user_id]["price"]
    conn = sqlite3.connect("/data/nomad_bot_new.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT location, capacity, price, contact FROM housing
        WHERE region = ? AND capacity >= ? AND price <= ?
        ORDER BY price ASC
    """, (region, capacity, price))
    results = cursor.fetchall()
    conn.close()
    if not results:
        await message.answer("🏠 По вашему запросу ничего не найдено.")
    else:
        text = "🏠 *Найденные варианты:*\n\n"
        for i, row in enumerate(results, 1):
            text += f"{i}. 📍 {row[0]}\n👥 {row[1]} чел.\n💰 {row[2]} сом/ночь\n📞 {row[3]}\n\n"
        await message.answer(text, parse_mode="Markdown")
    del search_data[user_id]

# ---- ЖИЛЬЁ: СДАТЬ ----
@dp.message(lambda message: message.text == "🏠 Сдать жильё")
async def add_housing_start(message: types.Message):
    user_id = message.from_user.id
    housing_data[user_id] = {"step": 0}
    await message.answer("📍 Введите город или локацию (например: Чолпон-Ата)")

@dp.message(lambda message: message.text == "🗑️ Удалить объявление")
async def delete_housing_start(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("/data/nomad_bot_new.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, location, price FROM housing WHERE user_id = ?", (user_id,))
    results = cursor.fetchall()
    conn.close()
    if not results:
        await message.answer("📭 У вас нет активных объявлений.")
        return
    text = "🗑️ *Ваши объявления:*\n\n"
    for row in results:
        text += f"🔹 {row[0]}. 📍 {row[1]} — {row[2]} сом/ночь\n"
    text += "\nНапишите номер объявления, которое хотите удалить."
    delete_data[user_id] = {"step": "waiting"}
    await message.answer(text, parse_mode="Markdown")

@dp.message(lambda message: message.text.isdigit() and message.from_user.id in delete_data)
async def delete_housing_confirm(message: types.Message):
    user_id = message.from_user.id
    listing_id = int(message.text)
    conn = sqlite3.connect("/data/nomad_bot_new.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM housing WHERE id = ?", (listing_id,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        await message.answer("❌ Объявление с таким номером не найдено.")
        return
    if result[0] != user_id:
        await message.answer("⛔ Это объявление принадлежит другому пользователю.")
        return
    conn = sqlite3.connect("/data/nomad_bot_new.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM housing WHERE id = ?", (listing_id,))
    conn.commit()
    conn.close()
    await message.answer("✅ Объявление удалено.")
    del delete_data[user_id]

# ---- БРОНИРОВАНИЕ ----
@dp.message(lambda message: message.text == "📅 Забронировать")
async def start_booking(message: types.Message):
    user_id = message.from_user.id
    booking_data[user_id] = {}
    await message.answer("🏠 Введите номер объявления, которое хотите забронировать (например: 1)")

@dp.message(lambda message: message.text.isdigit() and message.from_user.id in booking_data and "listing_id" not in booking_data[message.from_user.id])
async def get_booking_details(message: types.Message):
    user_id = message.from_user.id
    booking_data[user_id]["listing_id"] = int(message.text)
    await message.answer("📅 На сколько дней вы хотите забронировать?")

@dp.message(lambda message: message.text.isdigit() and message.from_user.id in booking_data and "days" not in booking_data[message.from_user.id])
async def save_booking(message: types.Message):
    user_id = message.from_user.id
    days = int(message.text)
    listing_id = booking_data[user_id]["listing_id"]
    conn = sqlite3.connect("/data/nomad_bot_new.db")
    cursor = conn.cursor()
    cursor.execute("SELECT contact, location FROM housing WHERE id = ?", (listing_id,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        await message.answer("❌ Объявление не найдено.")
        return
    host_contact, location = result
    conn = sqlite3.connect("/data/nomad_bot_new.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bookings (guest_id, guest_username, host_contact, location, days) VALUES (?, ?, ?, ?, ?)",
        (user_id, message.from_user.username or "unknown", host_contact, location, days)
    )
    conn.commit()
    conn.close()
    try:
        await bot.send_message(
            int(host_contact),
            f"🆕 *Новая заявка на бронирование!*\n\n📍 {location}\n👤 @{message.from_user.username}\n📅 {days} дней"
        )
    except:
        print("⚠️ Не удалось отправить уведомление хозяину")
    await message.answer("✅ Заявка отправлена!")
    del booking_data[user_id]

# ---- ОТЗЫВЫ ----
@dp.message(lambda message: message.text == "💬 Оставить мнение")
async def feedback_button(message: types.Message):
    await message.answer("📝 Напишите своё мнение — я сохраню его.")

@dp.message(lambda message: message.text == "❓ Помощь")
async def help_button(message: types.Message):
    await help_command(message)

# ---- ОБЩИЙ ОБРАБОТЧИК ----
@dp.message()
async def handle_all_messages(message: types.Message):
    user_id = message.from_user.id

    # ---- ФОРМА СДАЧИ ЖИЛЬЯ ----
    if user_id in housing_data:
        data = housing_data[user_id]
        step = data.get("step", 0)

        if step == 0:
            data["location"] = message.text
            data["step"] = "region"
            await message.answer("📍 К какому региону относится? Выберите:", reply_markup=region_buttons())
        elif step == "region":
            data["region"] = message.text
            data["step"] = 1
            await message.answer("👥 Сколько человек?", reply_markup=ReplyKeyboardRemove())
        elif step == 1:
            data["capacity"] = message.text
            data["step"] = 2
            await message.answer("💰 Цена за ночь (в сомах):")
        elif step == 2:
            data["price"] = message.text
            data["step"] = 3
            await message.answer("📞 Ваш номер телефона:")
        elif step == 3:
            data["contact"] = message.text
            data["step"] = 4
            await message.answer(
                f"📋 Проверьте данные:\n📍 {data['location']}\n🗺️ {data['region']}\n👥 {data['capacity']} чел.\n💰 {data['price']} сом\n📞 {data['contact']}\n\nВсё верно? Напишите «Да» или «Нет»"
            )
        elif step == 4:
            if message.text.lower() in ["да", "д", "yes", "y"]:
                conn = sqlite3.connect("/data/nomad_bot_new.db")
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO housing (user_id, location, region, capacity, price, contact) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, data["location"], data["region"], data["capacity"], data["price"], data["contact"])
                )
                conn.commit()
                conn.close()
                await message.answer("✅ Объявление сохранено!")
                del housing_data[user_id]
            else:
                await message.answer("❌ Отменено.")
                del housing_data[user_id]
        return

    # ---- СОХРАНЕНИЕ ОТЗЫВОВ ----
    with open("/data/feedback.txt", "a", encoding="utf-8") as f:
        f.write(message.text + "\n")
    await message.answer("🌾 Спасибо! Ваше мнение сохранено.")

async def main():
    init_db()
    print("👤 Администратор:", ADMIN_ID)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())




