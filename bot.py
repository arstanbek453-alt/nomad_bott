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

# =========================================
# 3. ХРАНИЛИЩЕ СОСТОЯНИЙ
# =========================================
user_state = {}

# =========================================
# 4. БАЗА ДАННЫХ
# =========================================
def init_db():
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()

    # Таблица для объявлений о жилье
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

    # Таблица для бронирований
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

    # Таблица для отзывов
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")


# =========================================
# 5. МЕНЮ И КНОПКИ
# =========================================
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

# =========================================
# 6. КОМАНДА /START
# =========================================
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        f"🏔️ Салам, {message.from_user.first_name}! Я — NomadConnect.",
        reply_markup=main_menu()
    )

# =========================================
# 7. ФУНКЦИИ: НАЙТИ ЖИЛЬЁ
# =========================================
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
    c = conn.cursor()
    c.execute("SELECT location, capacity, price, contact FROM housing WHERE region = ? AND capacity >= ? AND price <= ?", (data["region"], data["capacity"], data["price"]))
    results = c.fetchall()
    conn.close()
    if results:
        text = "🏠 *Найденные варианты:*\n\n"
        for i, row in enumerate(results, 1):
            text += f"{i}. 📍 {row[0]}\n👥 {row[1]} чел.\n💰 {row[2]} сом/ночь\n📞 {row[3]}\n\n"
        await message.answer(text, parse_mode="Markdown")
    else:
        await message.answer("🏠 По вашему запросу ничего не найдено.")
    del user_state[user_id]

# =========================================
# 8. ФУНКЦИИ: СДАТЬ ЖИЛЬЁ
# =========================================
@dp.message(lambda message: message.text == "🏠 Сдать жильё")
async def add_housing_start(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"mode": "add", "step": 0, "data": {}}
    await message.answer("📍 Введите город или локацию:")

@dp.message(lambda message: user_state.get(message.from_user.id, {}).get("mode") == "add" and user_state[message.from_user.id]["step"] == 0)
async def add_location(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["data"]["location"] = message.text
    user_state[user_id]["step"] = 1
    await message.answer("📍 К какому региону относится? Выберите:", reply_markup=region_buttons())

@dp.message(lambda message: message.text in ["Бишкек", "Ош", "Иссык-Куль (Север)", "Иссык-Куль (Юг)", "Чуй", "Талас", "Джалал-Абад", "Баткен"] and user_state.get(message.from_user.id, {}).get("mode") == "add" and user_state[message.from_user.id]["step"] == 1)
async def add_region(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["data"]["region"] = message.text
    user_state[user_id]["step"] = 2
    await message.answer("👥 Сколько человек?", reply_markup=ReplyKeyboardRemove())

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "add" and user_state[message.from_user.id]["step"] == 2)
async def add_capacity(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["data"]["capacity"] = int(message.text)
    user_state[user_id]["step"] = 3
    await message.answer("💰 Цена за ночь (в сомах):")

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "add" and user_state[message.from_user.id]["step"] == 3)
async def add_price(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["data"]["price"] = int(message.text)
    user_state[user_id]["step"] = 4
    await message.answer("📞 Ваш номер телефона:")

@dp.message(lambda message: user_state.get(message.from_user.id, {}).get("mode") == "add" and user_state[message.from_user.id]["step"] == 4)
async def add_contact(message: types.Message):
    user_id = message.from_user.id
    print(f"🔍 add_contact вызван для {user_id}")  # ← добавь эту строку
    print(f"🔍 user_state: {user_state}")           # ← и эту
    data = user_state[user_id]["data"]
    data["contact"] = message.text
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()
    c.execute("INSERT INTO housing (user_id, location, region, capacity, price, contact) VALUES (?, ?, ?, ?, ?, ?)", (user_id, data["location"], data["region"], data["capacity"], data["price"], data["contact"]))
    conn.commit()
    conn.close()
    await message.answer("✅ Объявление сохранено!")
    del user_state[user_id]

# =========================================
# 9. УДАЛЕНИЕ ОБЪЯВЛЕНИЯ
# =========================================
@dp.message(lambda message: message.text == "🗑️ Удалить объявление")
async def delete_start(message: types.Message):
    user_id = message.from_user.id
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()
    c.execute("SELECT id, location, price FROM housing WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        await message.answer("📭 У вас нет объявлений.")
        return
    text = "🗑️ *Ваши объявления:*\n\n"
    for row in rows:
        text += f"{row[0]}. 📍 {row[1]} — {row[2]} сом/ночь\n"
    text += "\nНапишите номер для удаления."
    user_state[user_id] = {"mode": "delete"}
    await message.answer(text, parse_mode="Markdown")

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "delete")
async def delete_confirm(message: types.Message):
    user_id = message.from_user.id
    listing_id = int(message.text)
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM housing WHERE id = ? AND user_id = ?", (listing_id, user_id))
    conn.commit()
    conn.close()
    await message.answer("✅ Объявление удалено.")
    del user_state[user_id]

# =========================================
# 10. БРОНИРОВАНИЕ
# =========================================
@dp.message(lambda message: message.text == "📅 Забронировать")
async def booking_start(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id] = {"mode": "book", "step": 0}
    await message.answer("🏠 Введите номер объявления:")

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "book" and user_state[message.from_user.id]["step"] == 0)
async def booking_listing(message: types.Message):
    user_id = message.from_user.id
    user_state[user_id]["listing_id"] = int(message.text)
    user_state[user_id]["step"] = 1
    await message.answer("📅 На сколько дней?")

@dp.message(lambda message: message.text.isdigit() and user_state.get(message.from_user.id, {}).get("mode") == "book" and user_state[message.from_user.id]["step"] == 1)
async def booking_save(message: types.Message):
    user_id = message.from_user.id
    days = int(message.text)
    listing_id = user_state[user_id]["listing_id"]
    conn = sqlite3.connect("nomad_bot.db")
    c = conn.cursor()
    c.execute("SELECT contact, location FROM housing WHERE id = ?", (listing_id,))
    row = c.fetchone()
    conn.close()
    if row:
        host_contact, location = row
        conn = sqlite3.connect("nomad_bot.db")
        c = conn.cursor()
        c.execute("INSERT INTO bookings (guest_id, guest_username, host_contact, location, days) VALUES (?, ?, ?, ?, ?)", (user_id, message.from_user.username or "unknown", host_contact, location, days))
        conn.commit()
        conn.close()
        await message.answer("✅ Заявка отправлена!")
    else:
        await message.answer("❌ Объявление не найдено.")
    del user_state[user_id]

# =========================================
# 11. ОТЗЫВЫ
# =========================================
@dp.message(lambda message: message.text == "💬 Оставить мнение")
async def feedback(message: types.Message):
    await message.answer("📝 Напишите своё мнение:")

@dp.message(lambda message: message.text == "❓ Помощь")
async def help_command(message: types.Message):
    await message.answer("Доступные команды:\n/start – Приветствие\n/help – Помощь")

# =========================================
# 12. AI АГЕНТ (ОБРАБОТКА ВСЕХ ОСТАЛЬНЫХ СООБЩЕНИЙ)
# =========================================
@dp.message()
async def agent_handler(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text

    print(f"📩 Сообщение от {user_id}: {user_text}")
    print(f"📊 user_state: {user_state}")

    # ---- ЕСЛИ ПОЛЬЗОВАТЕЛЬ В РЕЖИМЕ ПОИСКА ----
    if user_id in user_state and user_state[user_id].get("mode") == "search":
        step = user_state[user_id].get("step", 0)
        if step == 0:
            await search_region(message)
        elif step == 1:
            await search_capacity(message)
        elif step == 2:
            await search_price(message)
        return

    # ---- ЕСЛИ ПОЛЬЗОВАТЕЛЬ В РЕЖИМЕ ДОБАВЛЕНИЯ ----
    if user_id in user_state and user_state[user_id].get("mode") == "add":
        step = user_state[user_id].get("step", 0)
        if step == 0:
            await add_location(message)
        elif step == 1:
            await add_region(message)
        elif step == 2:
            await add_capacity(message)
        elif step == 3:
            await add_price(message)
        elif step == 4:
            await add_contact(message)
        return

    # ---- ЕСЛИ ПОЛЬЗОВАТЕЛЬ В РЕЖИМЕ БРОНИРОВАНИЯ ----
    if user_id in user_state and user_state[user_id].get("mode") == "book":
        step = user_state[user_id].get("step", 0)
        if step == 0:
            await booking_listing(message)
        elif step == 1:
            await booking_save(message)
        return

    # ---- ЕСЛИ ПОЛЬЗОВАТЕЛЬ В РЕЖИМЕ УДАЛЕНИЯ ----
    if user_id in user_state and user_state[user_id].get("mode") == "delete":
        await delete_confirm(message)
        return

    # ---- ЕСЛИ НЕТ АКТИВНОГО РЕЖИМА — ИСПОЛЬЗУЕМ AI ----
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": """
            You are NomadConnect assistant. Classify user intent:
            - 'search' → user wants to find accommodation
            - 'booking' → user wants to book
            - 'add' → user wants to list property
            - 'delete' → user wants to delete listing
            - 'general' → casual chat
            """},
            {"role": "user", "content": user_text}
        ]
    )

    reply = response.choices[0].message.content

    if "search" in reply.lower():
        await start_search(message)
    elif "booking" in reply.lower():
        await booking_start(message)
    elif "add" in reply.lower():
        await add_housing_start(message)
    elif "delete" in reply.lower():
        await delete_start(message)
    else:
        await message.answer(reply)

# =========================================
# 13. ЗАПУСК
# =========================================
async def main():
    init_db()
    print("✅ Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())








