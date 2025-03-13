import asyncio
import sqlite3
import logging
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import os

# Твой токен бота (бери из Render Environment Variables)
TOKEN = os.getenv("TOKEN")  

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
    await message.answer("Привет! Я бот для учета оценок.\n\n📌 Доступные команды:\n"
                         "/list - Список учеников\n"
                         "/top_week - Топ учеников за неделю\n"
                         "/top_month - Топ учеников за месяц\n"
                         "/top_alltime - Топ учеников за всё время\n"
                         "/add [оценка] [ID] - Добавить оценку\n"
                         "/remove_scores [ID] [кол-во] - Удалить баллы\n"
                         "/clear_scores [ID] - Очистить все оценки")

@dp.me
