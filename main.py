import asyncio
import sqlite3
import logging
import datetime
import shutil
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import os
import atexit

# Твой токен бота (бери из Render Environment Variables)
TOKEN = os.getenv("TOKEN")  

# ID администратора (замени на свой)
ADMIN_ID = 8177169682  

# ✅ Восстанавливаем базу данных, если она есть
if not os.path.exists("students.db"):
    open("students.db", "w").close()  # Создаём пустую базу, если её нет

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

# ✅ Авто-бэкап перед выходом
def backup_database():
    shutil.copy("students.db", "students.db.bak")
    print("✅ Авто-бэкап базы данных выполнен!")

atexit.register(backup_database)  # Бэкап при завершении работы

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

# ✅ Инициализация бота (исправлена ошибка `dp is not defined`)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ======================== КОМАНДЫ БОТА =========================

@dp.message(Command("start"))
async def start(message: Message):
    """Приветствие"""
    await message.answer("Привет! Я бот для учета оценок.\n\n📌 Доступные команды:\n"
                         "/list - Список учеников\n"
                         "/top - Топ учеников по сумме баллов\n"
                         "/add [оценка] [ID] - Добавить оценку\n"
                         "/remove_scores [ID] [кол-во] - Удалить баллы\n"
                         "/clear_scores [ID] - Очистить все оценки\n"
                         "/backup - Сохранить базу перед перезапуском")

@dp.message(Command("list"))
async def list_students(message: Message):
    """Выводит список всех учеников с их ID"""
    cursor.execute("SELECT id, name FROM students")
    students = cursor.fetchall()

    if students:
        result = "\n".join([f"{s[0]} - {s[1]}" for s in students])
        await message.answer(f"📋 Список учеников:\n{result}")
    else:
        await message.answer("📌 В базе нет учеников.")

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

# ======================== ТОП УЧЕНИКОВ =========================

@dp.message(Command("top"))
async def top_students(message: Message):
    """Выводит топ учеников по сумме всех оценок"""
    query = """
    SELECT students.id, students.name, COALESCE(SUM(scores.score), 0) as total_score 
    FROM students 
    LEFT JOIN scores ON students.id = scores.student_id
    GROUP BY students.id 
    ORDER BY total_score DESC 
    LIMIT 10
    """
    
    cursor.execute(query)
    top_students = cursor.fetchall()

    if not top_students:
        return await message.answer("⚠ В этом периоде нет данных для топа!")

    result = [f"{i+1}. {name} – {total_score} баллов" for i, (student_id, name, total_score) in enumerate(top_students)]
    await message.answer("🏆 Топ учеников по сумме всех оценок:\n" + "\n".join(result))

# ======================== УДАЛЕНИЕ БАЛЛОВ =========================

@dp.message(Command("remove_scores"))
async def remove_scores(message: Message):
    """Удаляет определённое количество баллов у ученика (только админ)"""
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

    # Получаем ID последних оценок ученика
    cursor.execute("SELECT id FROM scores WHERE student_id = ? ORDER BY id ASC LIMIT ?", (student_id, count))
    scores_to_delete = cursor.fetchall()

    if not scores_to_delete:
        return await message.answer("⚠ У этого ученика недостаточно баллов!")

    # Удаляем нужное количество оценок
    for score_id in scores_to_delete:
        cursor.execute("DELETE FROM scores WHERE id = ?", (score_id[0],))

    conn.commit()
    await message.answer(f"✅ Удалено {count} баллов у ученика с ID {student_id}!")

# ======================== СОХРАНЕНИЕ БАЗЫ =========================

@dp.message(Command("backup"))
async def backup_db(message: Message):
    """Сохраняет копию базы данных в GitHub"""
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ У вас нет прав!")

    shutil.copy("students.db", "backup_students.db")
    await message.answer("✅ База данных сохранена! Загрузите файл `backup_students.db` в GitHub перед перезапуском.")

# ======================== ЗАПУСК БОТА =========================
async def main():
    """Запуск бота"""
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
