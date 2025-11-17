from pymongo import MongoClient
from config import MONGO_URI
from datetime import datetime
from bson.objectid import ObjectId

client = MongoClient(MONGO_URI)
db = client.get_default_database()

users = db['users']
events = db['events']
stickers = db['stickers']

# --- User ---
def create_user(email, username, password_hash):
    return users.insert_one({
        "email": email,
        "username": username,
        "password_hash": password_hash,
        "created_at": datetime.utcnow()
    })

def get_user_by_email(email):
    return users.find_one({"email": email})

# --- Events ---
def create_event(user_id, title, start_time, end_time=None, category_id=None, sticker_id=None):
    return events.insert_one({
        "user_id": ObjectId(user_id),
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "category_id": category_id,
        "sticker_id": sticker_id,
        "is_completed": False,
        "created_at": datetime.utcnow()
    })

def get_events(user_id):
    return list(events.find({"user_id": ObjectId(user_id)}))

def update_event(event_id, data):
    events.update_one({"_id": ObjectId(event_id)}, {"$set": data})

def delete_event(event_id):
    events.delete_one({"_id": ObjectId(event_id)})

# --- Stickers ---
def create_sticker(name, image_url):
    return stickers.insert_one({
        "name": name,
        "image_url": image_url,
        "created_at": datetime.utcnow()
    })

def get_stickers():
    return list(stickers.find())
