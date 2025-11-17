from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from datetime import datetime
import os
import base64

auth_bp = Blueprint('auth', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    from app import mongo
    users = mongo.db.users

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        username = request.form.get('username', '')

        if users.find_one({"email": email}):
            flash("Користувач з таким email вже існує!")
            return render_template('register.html')

        hashed = generate_password_hash(password)
        users.insert_one({
            "email": email,
            "username": username,
            "password": hashed,
            "avatar": None,
            "theme": "pink",
            "completed_tasks": 0,
            "total_days": 0,
            "streak_days": 0,
            "avg_mood": 0,
            "created_at": datetime.utcnow()
        })

        flash("Реєстрація успішна! Увійдіть.")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    from app import mongo
    users = mongo.db.users

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users.find_one({"email": email})

        if not user or 'password' not in user or not check_password_hash(user['password'], password):
            flash("Невірний email або пароль!")
            return render_template('login.html')

        session['user_id'] = str(user['_id'])
        flash("Успішний вхід!")
        return redirect(url_for('planner.calendar_view'))

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Ви вийшли з системи.")
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    from app import mongo
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    users = mongo.db.users
    user_id = ObjectId(session['user_id'])
    user = users.find_one({"_id": user_id})

    if request.method == 'POST':
        username = request.form.get('username', user.get('username'))
        email = request.form.get('email', user.get('email'))
        new_password = request.form.get('new_password')
        theme = request.form.get('theme', 'pink')
        
        update_data = {
            "username": username,
            "email": email,
            "theme": theme
        }
        
        # Якщо вказано новий пароль
        if new_password:
            update_data['password'] = generate_password_hash(new_password)
        
        users.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        
        flash("Профіль оновлено")
        return redirect(url_for('auth.profile'))

    # Підрахунок статистики
    events = mongo.db.events
    daily_entries = mongo.db.daily_entries
    
    completed_tasks = events.count_documents({"user_id": user_id, "is_completed": True})
    total_days = daily_entries.count_documents({"user_id": user_id})
    
    # Середній настрій
    avg_mood_result = list(daily_entries.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$user_mood_rating"}}}
    ]))
    avg_mood = round(avg_mood_result[0]['avg'], 1) if avg_mood_result else 0
    
    # Підрахунок streak (днів підряд)
    streak_days = calculate_streak(user_id, daily_entries)
    
    # Оновлюємо статистику в профілі
    users.update_one(
        {"_id": user_id},
        {"$set": {
            "completed_tasks": completed_tasks,
            "total_days": total_days,
            "avg_mood": avg_mood,
            "streak_days": streak_days
        }}
    )
    
    user = users.find_one({"_id": user_id})
    return render_template('profile.html', user=user)
@auth_bp.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    if 'avatar' not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files['avatar']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    file_data = file.read()
    if len(file_data) > 2 * 1024 * 1024:
        return jsonify({"error": "File too large"}), 400

    extension = file.filename.rsplit('.', 1)[1].lower()
    mime_types = {'png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','gif':'image/gif','webp':'image/webp'}
    mime_type = mime_types.get(extension, 'image/png')
    avatar_url = f"data:{mime_type};base64,{base64.b64encode(file_data).decode('utf-8')}"

    from app import mongo
    user_id = ObjectId(session['user_id'])
    mongo.db.users.update_one({"_id": user_id}, {"$set": {"avatar": avatar_url}})

    return jsonify({"success": True, "avatar_url": avatar_url})

def calculate_streak(user_id, daily_entries_collection):
    entries = list(daily_entries_collection.find({"user_id": user_id}, {"date": 1}).sort("date", -1))
    if not entries:
        return 0

    streak = 0
    current_date = date.today()
    for entry in entries:
        entry_date = entry['date'].date() if isinstance(entry['date'], datetime) else datetime.strptime(entry['date'], "%Y-%m-%d").date()
        if entry_date == current_date:
            streak += 1
            current_date -= timedelta(days=1)
        elif entry_date == current_date - timedelta(days=1):
            streak += 1
            current_date = entry_date - timedelta(days=1)
        else:
            break
    return streak

def calculate_streak(user_id, daily_entries_collection):
    """Підрахунок кількості днів підряд"""
    from datetime import date, timedelta
    
    entries = list(daily_entries_collection.find(
        {"user_id": user_id},
        {"date": 1}
    ).sort("date", -1))
    
    if not entries:
        return 0
    
    streak = 0
    current_date = date.today()
    
    for entry in entries:
        entry_date = datetime.strptime(entry['date'], "%Y-%m-%d").date()
        
        if entry_date == current_date:
            streak += 1
            current_date -= timedelta(days=1)
        elif entry_date == current_date - timedelta(days=1):
            streak += 1
            current_date = entry_date - timedelta(days=1)
        else:
            break
    
    return streak
