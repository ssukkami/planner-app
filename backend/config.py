import os
from dotenv import load_dotenv

load_dotenv()

# Отримуємо базовий URI з .env
MONGO_BASE = os.getenv(
    "MONGO_URI",
    "mongodb+srv://planner_user:PlannerPass123@planner-cluster.ctf7tbq.mongodb.net/planner_db"
)

# Перевіряємо чи в URI вже є параметри
if "?" in MONGO_BASE:
    # Якщо є параметри, додаємо свої через &
    MONGO_URI = f"{MONGO_BASE}&tlsAllowInvalidCertificates=true&retryWrites=true&w=majority"
else:
    # Якщо нема, додаємо через ?
    MONGO_URI = f"{MONGO_BASE}?tlsAllowInvalidCertificates=true&retryWrites=true&w=majority"

# Flask Secret Key
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")

# Hugging Face API Key
HF_API_KEY = os.getenv("HF_API_KEY", "1234567")