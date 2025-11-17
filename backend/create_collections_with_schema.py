from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime

# Завантажуємо .env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Підключення до MongoDB
client = MongoClient(MONGO_URI)
db = client['planner_db']

# Шаблони документів для кожної колекції
collections_with_sample = {
    "users": {
        "user_id": 1,
        "email": "user@example.com",
        "username": "Ivan",
        "password_hash": "hashed_password",
        "created_at": datetime.utcnow()
    },
    "event_categories": {
        "category_id": 1,
        "name_ua": "Робота",
        "color_hex": "#FF5733"
    },
    "events": {
        "event_id": 1,
        "user_id": 1,
        "category_id": 1,
        "title": "Написати звіт",
        "description": "Звіт для керівника",
        "start_time": datetime(2025,11,12,9,0),
        "end_time": datetime(2025,11,12,11,0),
        "is_completed": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    "day_entries": {
        "entry_id": 1,
        "user_id": 1,
        "entry_date": datetime(2025,11,12),
        "user_description": "Продуктивний день",
        "submitted_at": datetime.utcnow(),
        "user_mood_rating": 8
    },
    "ai_analyses": {
        "analysis_id": 1,
        "entry_id": 1,
        "ai_mood_label_ua": "Радісний",
        "ai_summary_ua": "Продуктивний день, завершив всі завдання",
        "productivity_score": 95,
        "analysis_timestamp": datetime.utcnow()
    },
    "daily_statistics": {
        "stats_id": 1,
        "user_id": 1,
        "stat_date": datetime(2025,11,12),
        "total_events": 5,
        "completed_events": 4,
        "time_planned_minutes": 240
    }
}

# Створення колекцій та додавання шаблонних документів
for col, doc in collections_with_sample.items():
    if col not in db.list_collection_names():
        db.create_collection(col)
        print(f"Колекція '{col}' створена.")
    else:
        print(f"Колекція '{col}' вже існує.")
    db[col].insert_one(doc)
    print(f"Додано приклад документа у '{col}'.")

print("Всі колекції створено з атрибутами і прикладними документами.")
