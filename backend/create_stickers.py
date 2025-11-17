from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# --- Завантаження .env ---
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# --- Підключення до MongoDB ---
client = MongoClient(MONGO_URI)
db = client['planner_db']  # назва твоєї бази
stickers = db['stickers']  # колекція для стікерів

# --- Функція для створення стікера ---
def create_sticker(name, image_url):
    return stickers.insert_one({
        "name": name,
        "image_url": image_url,
        "created_at": datetime.utcnow()
    })

# --- Тестові стікери ---
sticker_list = [
    {"name": "Сонечко", "image_url": "https://i.imgur.com/abc123.png"},
    {"name": "Зірочка", "image_url": "https://i.imgur.com/xyz456.png"},
    {"name": "Смайлик", "image_url": "https://i.imgur.com/smile.png"}
]

# --- Додавання стікерів у колекцію ---
for s in sticker_list:
    create_sticker(s['name'], s['image_url'])

print("Колекція 'stickers' створена та заповнена тестовими даними!")
