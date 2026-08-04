import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

TOKEN = "8833304083:AAE92ZCznJuNakic46jZNzTBoDkUigqMWFo"
ADMIN_ID = 8144871993  # Замени на свой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---- ХРАНИЛИЩА СОСТОЯНИЙ ----
user_state = {}  # {user_id: {"mode": "search"|"add"|"delete"|"book", "step": 0, "data": {}}}

def init_db():
    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

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

# ---- СТАРТ ----
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, message.from_user.username or "unknown"))
    conn.commit()
    conn.close()
    await message.answer(f"🏔️ Салам, {message.from_user.first_name}! Я — NomadConnect.", reply_markup=main_menu())

# ---- НАЙТИ ЖИЛЬЁ ----
@dp.message(lambda message: message.text == "🏠 Найти жильё")
async def start_search(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"mode": "search", "step": 0}
    await message.answer("📍 Выберите регион:", reply_markup=region_buttons())

@dp.message(lambda message: message.text in ["Бишкек", "Ош", "Иссык-Куль (Север)", "Иссык-Куль (Юг)", "Чуй", "Талас", "Джалал-Абад", "Баткен"] and user_state.get(message.from_user.id, {}).get("mode") == "search" and user_state[message.from_user.id]["step"] == 0)
async def search_region(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["data"] = {"region": message.text}
    user_state[user_id]["step"] = 1
    await message.answer("👥 Сколько человек?", reply_markup=ReplyKeyboardRemove())

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "search" and user_state[message.from_user.id]["step"] == 1)
async def search_capacity(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["data"]["capacity"] = int(message.text)
    user_state[user_id]["step"] = 2
    await message.answer("💰 Максимальная цена за ночь (в сомах):")

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "search" and user_state[message.from_user.id]["step"] == 2)
async def search_price(message: types.Message):
    user_id = message.from_user.id
    data = user_state[user_id]["data"]
    data["price"] = int(message.text)

    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT location, capacity, price, contact FROM housing
        WHERE region = ? AND capacity >= ? AND price <= ?
    """, (data["region"], data["capacity"], data["price"]))
    results = cursor.fetchall()
    conn.close()

    if not results:
        await message.answer("🏠 По вашему запросу ничего не найдено.")
    else:
        text = "🏠 *Найденные варианты:*\n\n"
        for i, row in enumerate(results, 1):
            text += f"{i}. 📍 {row[0]}\n👥 {row[1]} чел.\n💰 {row[2]} сом/ночь\n📞 {row[3]}\n\n"
        await message.answer(text, parse_mode="Markdown")

    del user_state[user_id]

# ---- СДАТЬ ЖИЛЬЁ ----
@dp.message(lambda message: message.text == "🏠 Сдать жильё")
async def add_housing_start(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"mode": "add", "step": 0, "data": {}}
    await message.answer("📍 Введите город или локацию:")

@dp.message(lambda message: user_state.get(message.from_user.id, {}).get("mode") == "add" and user_state[message.from_user.id]["step"] == 0)
async def add_housing_location(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["data"]["location"] = message.text
    user_state[user_id]["step"] = 1
    await message.answer("📍 К какому региону относится? Выберите:", reply_markup=region_buttons())

@dp.message(lambda message: message.text in ["Бишкек", "Ош", "Иссык-Куль (Север)", "Иссык-Куль (Юг)", "Чуй", "Талас", "Джалал-Абад", "Баткен"] and user_state.get(message.from_user.id, {}).get("mode") == "add" and user_state[message.from_user.id]["step"] == 1)
async def add_housing_region(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["data"]["region"] = message.text
    user_state[user_id]["step"] = 2
    await message.answer("👥 Сколько человек?", reply_markup=ReplyKeyboardRemove())

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "add" and user_state[message.from_user.id]["step"] == 2)
async def add_housing_capacity(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["data"]["capacity"] = int(message.text)
    user_state[user_id]["step"] = 3
    await message.answer("💰 Цена за ночь (в сомах):")

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "add" and user_state[message.from_user.id]["step"] == 3)
async def add_housing_price(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["data"]["price"] = int(message.text)
    user_state[user_id]["step"] = 4
    await message.answer("📞 Ваш номер телефона:")

@dp.message(lambda message: user_state.get(message.from_user.id, {}).get("mode") == "add" and user_state[message.from_user.id]["step"] == 4)
async def add_housing_contact(message: types.Message):
    user_id = message.from_user.id
    data = user_state[user_id]["data"]
    data["contact"] = message.text

    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO housing (user_id, location, region, capacity, price, contact) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, data["location"], data["region"], data["capacity"], data["price"], data["contact"])
    )
    conn.commit()
    conn.close()

    await message.answer("✅ Объявление сохранено!")
    del user_state[user_id]

# ---- УДАЛИТЬ ОБЪЯВЛЕНИЕ ----
@dp.message(lambda message: message.text == "🗑️ Удалить объявление")
async def delete_housing_start(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("nomad_bot.db")
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

    user_state[user_id] = {"mode": "delete", "step": 0}
    await message.answer(text, parse_mode="Markdown")

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "delete")
async def delete_housing_confirm(message: types.Message):
    user_id = message.from_user.id
    listing_id = int(message.text)

    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM housing WHERE id = ?", (listing_id,))
    result = cursor.fetchone()
    conn.close()

    if not result or result[0] != user_id:
        await message.answer("❌ Объявление не найдено или не принадлежит вам.")
        return

    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM housing WHERE id = ?", (listing_id,))
    conn.commit()
    conn.close()

    await message.answer("✅ Объявление удалено.")
    del user_state[user_id]

# ---- БРОНИРОВАНИЕ ----
@dp.message(lambda message: message.text == "📅 Забронировать")
async def start_booking(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"mode": "book", "step": 0}
    await message.answer("🏠 Введите номер объявления, которое хотите забронировать:")

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "book" and user_state[message.from_user.id]["step"] == 0)
async def book_get_listing(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["listing_id"] = int(message.text)
    user_state[user_id]["step"] = 1
    await message.answer("📅 На сколько дней?")

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "book" and user_state[message.from_user.id]["step"] == 1)
async def save_booking(message: types.Message):
    user_id = message.from_user.id
    days = int(message.text)
    listing_id = user_state[user_id]["listing_id"]

    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT contact, location FROM housing WHERE id = ?", (listing_id,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        await message.answer("❌ Объявление не найдено.")
        del user_state[user_id]
        return

    host_contact, location = result

    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bookings (guest_id, guest_username, host_contact, location, days) VALUES (?, ?, ?, ?, ?)",
        (user_id, message.from_user.username or "unknown", host_contact, location, days)
    )
    conn.commit()
    conn.close()

    await message.answer("✅ Заявка отправлена!")
    del user_state[user_id]

# ---- ОТЗЫВЫ ----
@dp.message(lambda message: message.text == "💬 Оставить мнение")
async def feedback_button(message: types.Message):
    await message.answer("📝 Напишите своё мнение — я сохраню его.")

# ---- ПОМОЩЬ ----
@dp.message(lambda message: message.text == "❓ Помощь")
async def help_button(message: types.Message):
    await message.answer("Доступные команды:\n/start – Приветствие\n/help – Помощь")

# ---- ОБЩИЙ ОБРАБОТЧИК (ТОЛЬКО ДЛЯ ОТЗЫВОВ) ----
@dp.message()
async def save_feedback(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_state:
        return
    with open("feedback.txt", "a", encoding="utf-8") as f:
        f.write(message.text + "\n")
    await message.answer("🌾 Спасибо! Ваше мнение сохранено.")

async def main():
    init_db()
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())







