import asyncio
import sqlite3
import logging
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Твой токен бота
TOKEN = "7308160665:AAFjQ2st_AbQKNekJGVNyVj-iG8ymTgIWVs"

# ID администратора (замени на свой)
ADMIN_ID = 8177169682  

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключение к базе данных
conn = sqlite3.connect("students.db")
cursor = conn.cursor()

# Создаём таблицы, если их нет
cursor.execute("""CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    score INTEGER,
    date TEXT,
    FOREIGN KEY (student_id) REFERENCES students (id)
)""")
conn.commit()

# ======================== ДОБАВЛЕНИЕ СПИСКА УЧЕНИКОВ =========================
students = [
    "Азим", "Сабина", "Рахимжон", "Костя", "Камиля", "Богдан", "Б. Максим", "Настя",
    "Илья", "Тамерлан", "Алем", "Алексей", "Дания", "Темирлан", "Милана", "Рамилия",
    "Айбек", "Альмира", "Айсара", "Алёна", "Акбаян", "Арсен", "Аида", "Карина", 
    "Эльвира", "Биржан", "Максим", "Жуман", "Малика", "Даниил", "Алем"
]

for name in students:
    cursor.execute("INSERT OR IGNORE INTO students (name) VALUES (?)", (name,))
conn.commit()

# ======================== КОМАНДЫ БОТА =========================

@dp.message(Command("start"))
async def start(message: Message):
    """Приветствие"""
    await message.answer("Привет! Я бот Жумана,создве для трекинга оценок. \nКоманды: \n/list - список учеников\n/top - топ учеников.")

@dp.message(Command("list"))
async def list_students(message: Message):
    """Выводит список учеников с ID"""
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()

    if students:
        result = "\n".join([f"{s[0]} - {s[1]}" for s in students])
        await message.answer(f"📋 Список учеников:\n{result}")
    else:
        await message.answer("Список учеников пуст.")

@dp.message(Command("add"))
async def add_score(message: Message):
    """Добавление оценки ученику по ID (только админ)"""
    if message.from_user.id != ADMIN_ID:
        return await message.answer("У вас нет прав.")

    args = message.text.split()
    if len(args) < 3:
        return await message.answer("Использование: /add [оценка] [ID ученика]\nПример: /add 10 5")

    try:
        score = int(args[1])
        student_id = int(args[2])
    except ValueError:
        return await message.answer("Ошибка: Оценка и ID должны быть числами.")

    if not (1 <= score <= 10):
        return await message.answer("Ошибка: Оценка должна быть от 1 до 10.")

    cursor.execute("SELECT name FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()

    if student:
        student_name = student[0]
        today = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO scores (student_id, score, date) VALUES (?, ?, ?)", (student_id, score, today))
        conn.commit()
        await message.answer(f"✅ Оценка {score} добавлена для {student_name} (ID: {student_id}).")
    else:
        await message.answer("Ошибка: Ученик с таким ID не найден.")
@dp.message(Command("top"))
async def ask_top_period(message: Message):
    """Запрашивает у пользователя, за какой период показать топ"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Топ за неделю"), KeyboardButton(text="Топ за месяц")],
            [KeyboardButton(text="Топ за все время")]
        ],
        resize_keyboard=True
    )
    
    await message.answer("Выберите период:", reply_markup=keyboard)

@dp.message(F.text.in_(["Топ за неделю", "Топ за месяц", "Топ за все время"]))
async def top_students(message: Message):
    """Выводит топ учеников за выбранный период"""
    period_map = {
        "Топ за неделю": "date >= date('now', '-7 days')",
        "Топ за месяц": "date >= date('now', '-1 month')",
        "Топ за все время": "1=1"
    }
    
    period = message.text
    date_filter = period_map.get(period, "1=1")

    query = f"SELECT student_id, AVG(score) as avg_score FROM scores WHERE {date_filter} GROUP BY student_id ORDER BY avg_score DESC LIMIT 10"
    cursor.execute(query)
    top_students = cursor.fetchall()

    if not top_students:
        return await message.answer("Пока нет данных.")

    result = []
    for i, (student_id, avg_score) in enumerate(top_students, start=1):
        cursor.execute("SELECT name FROM students WHERE id = ?", (student_id,))
        student_name = cursor.fetchone()[0]
        result.append(f"{i}. {student_name} - {round(avg_score, 2)}")

    await message.answer(f"🏆 {period}:\n" + "\n".join(result))

# ======================== ЗАПУСК БОТА =========================
async def main():
    """Запуск бота"""
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
