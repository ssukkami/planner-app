import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB URI - додаємо ssl=false для обходу SSL проблеми на Render
MONGO_BASE = os.getenv(
    "MONGO_URI",
    "mongodb+srv://planner_user:PlannerPass123@planner-cluster.ctf7tbq.mongodb.net/planner_db"
)

# Додаємо параметри для обходу SSL на Render
MONGO_URI = f"{MONGO_BASE}?ssl=false&retryWrites=true&w=majority"

# Flask Secret Key
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")

# Hugging Face API Key
HF_API_KEY = os.getenv("HF_API_KEY", "1234567")