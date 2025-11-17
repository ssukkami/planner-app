from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Завантажуємо .env
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

# Підключення до MongoDB
client = MongoClient(MONGO_URI)

# Вибираємо базу даних
db = client['planner_db']

# Список колекцій для створення
collections = [
    'users',
    'event_categories',
    'events',
    'day_entries',
    'ai_analyses',
    'daily_statistics'
]

# Створюємо колекції, якщо їх ще немає
for col in collections:
    if col not in db.list_collection_names():
        db.create_collection(col)
        print(f"Колекція '{col}' створена!")
    else:
        print(f"Колекція '{col}' вже існує.")

print("Всі колекції готові до використання.")
