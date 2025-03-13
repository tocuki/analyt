import asyncio
import sqlite3
import logging
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import os

# Твой токен бота
TOKEN = os.getenv("TOKEN")  # Теперь Render сам подтянет токен из ENV переменной

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
    id INTEGER PRIMARY KEY,
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

# ======================== КОМАНДЫ БОТА =========================

@dp.message(Command("start"))
async def start(message: Message):
    """Приветствие"""
    await message.answer("Привет! Я бот для учета оценок. \nКоманды: \n/list - список учеников\n/top - топ учеников.")

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
        return await message.answer("⛔ У вас нет прав.")

    args = message.text.split()
    if len(args) < 3:
        return await message.answer("⚠ Использование: /add [оценка] [ID ученика]\nПример: /add 10 5")

    try:
        score = int(args[1])
        student_id = int(args[2])
    except ValueError:
        return await message.answer("⚠ Ошибка: Оценка и ID должны быть числами!")

    if not (1 <= score <= 10):
        return await message.answer("⚠ Ошибка: Оценка должна быть от 1 до 10!")

    cursor.execute("SELECT name FROM students WHERE id = ?", (student_id,))
    student = cursor.fetchone()

    if student:
        student_name = student[0]
        today = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO scores (student_id, score, date) VALUES (?, ?, ?)", (student_id, score, today))
        conn.commit()
        await message.answer(f"✅ Оценка {score} добавлена для {student_name} (ID: {student_id})!")
    else:
        await message.answer("⚠ Ошибка: Ученик с таким ID не найден!")

@dp.message(Command("remove_scores"))
async def remove_scores(message: Message):
    """Удаляет определённое количество оценок у ученика (только админ)"""
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ У вас нет прав!")

    args = message.text.split()
    if len(args) < 3:
        return await message.answer("⚠ Использование: /remove_scores [ID ученика] [Количество баллов]\nПример: /remove_scores 5 2")

    try:
        student_id = int(args[1])
        count = int(args[2])
    except ValueError:
        return await message.answer("⚠ Ошибка: ID и количество должны быть числами!")

    cursor.execute("SELECT id FROM scores WHERE student_id = ? ORDER BY id DESC LIMIT ?", (student_id, count))
    scores_to_delete = cursor.fetchall()

    if not scores_to_delete:
        return await message.answer("⚠ У этого ученика недостаточно оценок!")

    for score_id in scores_to_delete:
        cursor.execute("DELETE FROM scores WHERE id = ?", (score_id[0],))

    conn.commit()
    await message.answer(f"✅ Удалено {count} баллов у ученика с ID {student_id}!")

@dp.message(Command("clear_scores"))
async def clear_scores(message: Message):
    """Полностью удаляет все оценки ученика (только админ)"""
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ У вас нет прав на очистку оценок!")

    args = message.text.split()
    if len(args) < 2:
        return await message.answer("⚠ Использование: /clear_scores [ID ученика]\nПример: /clear_scores 5")

    try:
        student_id = int(args[1])
    except ValueError:
        return await message.answer("⚠ Ошибка: ID должен быть числом!")

    cursor.execute("DELETE FROM scores WHERE student_id = ?", (student_id,))
    conn.commit()

    await message.answer(f"✅ Все оценки ученика с ID {student_id} были удалены!")

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

    query = f"""
    SELECT student_id, AVG(score) as avg_score 
    FROM scores 
    WHERE {date_filter} 
    GROUP BY student_id 
    HAVING COUNT(score) > 0
    ORDER BY avg_score DESC 
    LIMIT 10
    """
    
    cursor.execute(query)
    top_students = cursor.fetchall()

    if not top_students:
        return await message.answer("⚠ В этом периоде нет данных для топа!")

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
