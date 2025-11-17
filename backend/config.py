import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
HF_API_KEY = os.getenv("HF_API_KEY", "1234567")
