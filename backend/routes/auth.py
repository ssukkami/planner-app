from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from datetime import datetime, date, timedelta
import base64

auth_bp = Blueprint('auth', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    db = current_app.config['db']
    users = db.users

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        username = request.form.get('username', '').strip()

        # Валідація
        if not email or not password:
            flash("Email та пароль обов'язкові!")
            return render_template('register.html')

        if users.find_one({"email": email}):
            flash("Користувач з таким email вже існує!")
            return render_template('register.html')

        hashed = generate_password_hash(password)
        try:
            users.insert_one({
                "email": email,
                "username": username or email.split('@')[0],
                "password": hashed,
                "avatar": None,
                "theme": "pink",
                "completed_tasks": 0,
                "total_days": 0,
                "streak_days": 0,
                "avg_mood": 0,
                "created_at": datetime.utcnow()
            })
        except Exception as e:
            print(f"ERROR register: {e}")
            flash("Помилка при реєстрації")
            return render_template('register.html')

        flash("Реєстрація успішна! Увійдіть.")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    db = current_app.config['db']
    users = db.users

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash("Email та пароль обов'язкові!")
            return render_template('login.html')

        try:
            user = users.find_one({"email": email})
        except Exception as e:
            print(f"ERROR login database: {e}")
            flash("Помилка при підключенні до БД")
            return render_template('login.html')

        if not user or not check_password_hash(user.get('password', ''), password):
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
    db = current_app.config['db']
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    users = db.users
    try:
        user_id = ObjectId(session['user_id'])
    except Exception:
        session.pop('user_id', None)
        return redirect(url_for('auth.login'))

    user = users.find_one({"_id": user_id})
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form.get('username', user.get('username', '')).strip()
        email = request.form.get('email', user.get('email', '')).strip()
        new_password = request.form.get('new_password', '').strip()
        theme = request.form.get('theme', 'pink')
        
        if not email:
            flash("Email обов'язковий!")
            return redirect(url_for('auth.profile'))

        update_data = {
            "username": username or email.split('@')[0],
            "email": email,
            "theme": theme
        }
        
        if new_password:
            update_data['password'] = generate_password_hash(new_password)
        
        try:
            users.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            flash("Профіль оновлено")
        except Exception as e:
            print(f"ERROR updating profile: {e}")
            flash("Помилка при оновленні профілю")
        
        return redirect(url_for('auth.profile'))

    # Підрахунок статистики
    try:
        events = db.events
        daily_entries = db.daily_entries
        
        completed_tasks = events.count_documents({"user_id": user_id, "is_completed": True})
        total_days = daily_entries.count_documents({"user_id": user_id})
        
        # Середній настрій
        avg_mood_result = list(daily_entries.aggregate([
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "avg": {"$avg": "$user_mood_rating"}}}
        ]))
        avg_mood = round(avg_mood_result[0]['avg'], 1) if avg_mood_result else 0
        
        # Підрахунок streak
        streak_days = calculate_streak(user_id, daily_entries)
        
        # Оновлюємо статистику
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
    except Exception as e:
        print(f"ERROR calculating stats: {e}")

    return render_template('profile.html', user=user)


@auth_bp.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'avatar' not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files['avatar']
    if not file or file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    try:
        file_data = file.read()
        if len(file_data) > 2 * 1024 * 1024:
            return jsonify({"error": "File too large (max 2MB)"}), 400

        extension = file.filename.rsplit('.', 1)[1].lower()
        mime_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        mime_type = mime_types.get(extension, 'image/png')
        avatar_url = f"data:{mime_type};base64,{base64.b64encode(file_data).decode('utf-8')}"

        db = current_app.config['db']
        user_id = ObjectId(session['user_id'])
        db.users.update_one({"_id": user_id}, {"$set": {"avatar": avatar_url}})

        return jsonify({"success": True, "avatar_url": avatar_url})
    except Exception as e:
        print(f"ERROR uploading avatar: {e}")
        return jsonify({"error": "Upload failed"}), 500


def calculate_streak(user_id, daily_entries_collection):
    """Підрахунок кількості днів підряд"""
    try:
        entries = list(daily_entries_collection.find(
            {"user_id": user_id},
            {"date": 1}
        ).sort("date", -1).limit(100))  # Ліміт для оптимізації
        
        if not entries:
            return 0
        
        streak = 0
        current_date = date.today()
        
        for entry in entries:
            entry_date = entry.get('date')
            if not entry_date:
                continue
            
            # Безпечна обробка дати
            if isinstance(entry_date, datetime):
                entry_date = entry_date.date()
            elif isinstance(entry_date, str):
                try:
                    entry_date = datetime.strptime(entry_date, "%Y-%m-%d").date()
                except Exception:
                    continue
            else:
                continue
            
            if entry_date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            elif entry_date == current_date - timedelta(days=1):
                streak += 1
                current_date = entry_date - timedelta(days=1)
            else:
                break
        
        return streak
    except Exception as e:
        print(f"ERROR calculating streak: {e}")
        return 0