import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import os

# ✅ Берём токен из Environment Variables (для Render)
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("⛔ Ошибка: Токен бота не найден! Добавь его в Render Environment Variables.")

# ✅ Фиксированный список учеников с ID, именем и 0 баллами (можно менять перед запуском)
students = {
    1: {"name": "Азим", "score": 0},
    2: {"name": "Сабина", "score": 0},
    3: {"name": "Рахимжон", "score": 0},
    4: {"name": "Костя", "score": 0},
    5: {"name": "Камиля", "score": 0},
    6: {"name": "Богдан", "score": 0},
    7: {"name": "Максим", "score": 0},
    8: {"name": "Настя", "score": 54},
    9: {"name": "Илья", "score": 19},
    10: {"name": "Тамерлан", "score": 39},
    11: {"name": "Алем", "score": 50},
    12: {"name": "Алексей", "score": 0},
    13: {"name": "Дания", "score": 0},
    14: {"name": "Темирлан", "score": 0},
    15: {"name": "Милана", "score": 0},
    16: {"name": "Рамилия", "score": 0},
    17: {"name": "Айбек", "score": 0},
    18: {"name": "Альмира", "score": 0},
    19: {"name": "Айсара", "score": 58},
    20: {"name": "Алёна", "score": 29},
    21: {"name": "Акбаян", "score": 0},
    22: {"name": "Арсен", "score": 57},
    23: {"name": "Аида", "score": 0},
    24: {"name": "Карина", "score": 0},
    25: {"name": "Эльвира", "score": 0},
    26: {"name": "Биржан", "score": 0},
    27: {"name": "Жуман", "score": 45},
    28: {"name": "Малика", "score": 0},
    29: {"name": "Даниил", "score": 0}
}

# ✅ Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ======================== КОМАНДЫ БОТА =========================

@dp.message(Command("start"))
async def start(message: Message):
    """Приветствие"""
    await message.answer("Привет! Я бот для учета оценок.\n\n📌 Доступные команды:\n"
                         "/list - Список учеников\n"
                         "/top - Топ учеников по сумме баллов")

@dp.message(Command("list"))
async def list_students(message: Message):
    """Выводит список всех учеников"""
    result = "\n".join([f"{sid}. {s['name']} – {s['score']} баллов" for sid, s in students.items()])
    await message.answer(f"📋 Список учеников:\n{result}")

@dp.message(Command("top"))
async def top_students(message: Message):
    """Выводит топ учеников по сумме всех оценок"""
    sorted_students = sorted(students.items(), key=lambda x: x[1]["score"], reverse=True)[:10]
    result = [f"{i+1}. {s['name']} – {s['score']} баллов" for i, (sid, s) in enumerate(sorted_students)]
    await message.answer("🏆 Топ учеников по сумме всех оценок:\n" + "\n".join(result))

# ======================== ЗАПУСК БОТА =========================
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
