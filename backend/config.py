import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB URI - просто як є, без змін
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://planner_user:PlannerPass123@planner-cluster.ctf7tbq.mongodb.net/planner_db?retryWrites=true&w=majority"
)

# Flask Secret Key
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")

# Hugging Face API Key
HF_API_KEY = os.getenv("HF_API_KEY", "1234567")