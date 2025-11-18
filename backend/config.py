import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB URI з додатковими SSL параметрами для Render
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://planner_user:PlannerPass123@planner-cluster.ctf7tbq.mongodb.net/planner_db?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"
)

# Переконуємося, що URI містить потрібні параметри SSL
if "tlsAllowInvalidCertificates" not in MONGO_URI:
    if "?" in MONGO_URI:
        MONGO_URI = f"{MONGO_URI}&tlsAllowInvalidCertificates=true"
    else:
        MONGO_URI = f"{MONGO_URI}?tlsAllowInvalidCertificates=true"

# Flask Secret Key
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")

# Hugging Face API Key
HF_API_KEY = os.getenv("HF_API_KEY", "1234567")