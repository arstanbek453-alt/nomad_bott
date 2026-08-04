import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

TOKEN = "8833304083:AAE92ZCznJuNakic46jZNzTBoDkUigqMWFo"
ADMIN_ID = 8144871993  # Замени на свой Telegram ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---- ХРАНИЛИЩА ----
housing_data = {}
search_data = {}
delete_data = {}
booking_data = {}

# ---- БАЗА ДАННЫХ ----
def init_db():
    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

# ---- МЕНЮ ----
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
    regions = ["🏙️ Бишкек", "🏙️ Ош", "🏞️ Иссык-Куль (Север)", "🏞️ Иссык-Куль (Юг)", "🌾 Чуй", "🌿 Талас", "🌄 Джалал-Абад", "🏜️ Баткен"]
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

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("Доступные команды:\n/start – Приветствие\n/help – Помощь")

# ---- НАЙТИ ЖИЛЬЁ ----
@dp.message(lambda message: message.text == "🏠 Найти жильё")
async def start_search(message: types.Message):
    user_id = message.from_user.id
    search_data[user_id] = {"step": "region"}
    await message.answer("📍 Выберите регион:", reply_markup=region_buttons())

@dp.message(lambda message: message.text in ["🏙️ Бишкек", "🏙️ Ош", "🏞️ Иссык-Куль (Север)", "🏞️ Иссык-Куль (Юг)", "🌾 Чуй", "🌿 Талас", "🌄 Джалал-Абад", "🏜️ Баткен"] and message.from_user.id in search_data and message.from_user.id not in housing_data)
async def search_region(message: types.Message):
    user_id = message.from_user.id
    search_data[user_id]["region"] = message.text
    search_data[user_id]["step"] = "capacity"
    await message.answer("👥 Сколько человек?", reply_markup=ReplyKeyboardRemove())

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
    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT location, capacity, price, contact FROM housing WHERE region = ? AND capacity >= ? AND price <= ?", (region, capacity, price))
    results = cursor.fetchall()
    conn.close()
    if not results:
        await message.answer("🏠 Ничего не найдено.")
    else:
        text = "🏠 *Найденные варианты:*\n\n"
        for i, row in enumerate(results, 1):
            text += f"{i}. 📍 {row[0]}\n👥 {row[1]} чел.\n💰 {row[2]} сом/ночь\n📞 {row[3]}\n\n"
        await message.answer(text, parse_mode="Markdown")
    del search_data[user_id]

# ---- СДАТЬ ЖИЛЬЁ ----
@dp.message(lambda message: message.text == "🏠 Сдать жильё")
async def add_housing_start(message: types.Message):
    user_id = message.from_user.id
    housing_data[user_id] = {"step": 0}
    await message.answer("📍 Введите город или локацию:")

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
        await message.answer("📭 У вас нет объявлений.")
        return
    text = "🗑️ *Ваши объявления:*\n\n"
    for row in results:
        text += f"🔹 {row[0]}. 📍 {row[1]} — {row[2]} сом/ночь\n"
    text += "\nНапишите номер для удаления."
    delete_data[user_id] = {"step": "waiting"}
    await message.answer(text, parse_mode="Markdown")

@dp.message(lambda message: message.text.isdigit() and message.from_user.id in delete_data)
async def delete_housing_confirm(message: types.Message):
    user_id = message.from_user.id
    listing_id = int(message.text)
    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM housing WHERE id = ?", (listing_id,))
    result = cursor.fetchone()
    conn.close()
    if not result or result[0] != user_id:
        await message.answer("❌ Не найдено или не ваше.")
        return
    conn = sqlite3.connect("nomad_bot.db")
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
    await message.answer("🏠 Введите номер объявления:")

@dp.message(lambda message: message.text.isdigit() and message.from_user.id in booking_data and "listing_id" not in booking_data[message.from_user.id])
async def get_booking_details(message: types.Message):
    user_id = message.from_user.id
    booking_data[user_id]["listing_id"] = int(message.text)
    await message.answer("📅 На сколько дней?")

@dp.message(lambda message: message.text.isdigit() and message.from_user.id in booking_data and "days" not in booking_data[message.from_user.id])
async def save_booking(message: types.Message):
    user_id = message.from_user.id
    days = int(message.text)
    listing_id = booking_data[user_id]["listing_id"]
    conn = sqlite3.connect("nomad_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT contact, location FROM housing WHERE id = ?", (listing_id,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        await message.answer("❌ Объявление не найдено.")
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
                f"📋 Проверьте:\n📍 {data['location']}\n🗺️ {data['region']}\n👥 {data['capacity']} чел.\n💰 {data['price']} сом\n📞 {data['contact']}\n\nВсё верно? Напишите «Да» или «Нет»"
            )
        elif step == 4:
            if message.text.lower() in ["да", "д"]:
                conn = sqlite3.connect("nomad_bot.db")
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

    with open("feedback.txt", "a", encoding="utf-8") as f:
        f.write(message.text + "\n")
    await message.answer("🌾 Спасибо! Ваше мнение сохранено.")

async def main():
    init_db()
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())






