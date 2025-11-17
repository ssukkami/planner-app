from flask import Blueprint, render_template, request, redirect, url_for, session, current_app, jsonify
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import calendar

planner_bp = Blueprint('planner', __name__, url_prefix='/planner')

# iOS emoji стилізація: добавляємо font-variant-emoji для iOS-подібного рендеру
AVAILABLE_STICKERS = ['🎉', '⭐', '❤️', '🔥', '💪', '🎯', '✨', '🌟', '💖', '🎈',
                      '🏆', '🎨', '📚', '☕', '🌈', '🦄', '🌸', '🍕', '🎮', '🎵']

# Категорії за замовчуванням (якщо користувач не створив свої)
DEFAULT_CATEGORIES = [
    {"name_ua": "Робота", "icon": "💼", "color_hex": "#FF5733"},
    {"name_ua": "Особисте", "icon": "🏠", "color_hex": "#33C3FF"},
    {"name_ua": "Спорт", "icon": "💪", "color_hex": "#4CAF50"},
    {"name_ua": "Навчання", "icon": "📚", "color_hex": "#9C27B0"},
    {"name_ua": "Здоров'я", "icon": "🏥", "color_hex": "#FF9800"},
    {"name_ua": "Розваги", "icon": "🎮", "color_hex": "#E91E63"},
]

def build_datetime_from(date_str, time_str=None):
    """Створює timezone-naive datetime об'єкт з дати та часу (формат date: YYYY-MM-DD, time: HH:MM)."""
    if not date_str:
        raise ValueError("date_str required")
    if not time_str:
        # повертаємо дату з 00:00 як час
        return datetime.strptime(date_str, "%Y-%m-%d")
    dt_str = f"{date_str} {time_str}"
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except ValueError:
        # fallback: якщо час некоректний, повертаємо без часу
        return datetime.strptime(date_str, "%Y-%m-%d")

def ensure_user_categories(user_id):
    """Створює категорії за замовчуванням для нового користувача (user_id — ObjectId)."""
    db = current_app.config['db']
    existing = db.event_categories.find_one({"user_id": user_id})
    
    if not existing:
        docs = []
        now = datetime.utcnow()
        for cat in DEFAULT_CATEGORIES:
            docs.append({
                "user_id": user_id,
                "name_ua": cat["name_ua"],
                "icon": cat["icon"],
                "color_hex": cat["color_hex"],
                "created_at": now
            })
        if docs:
            db.event_categories.insert_many(docs)

def get_user_categories(user_id):
    """Отримує всі категорії користувача, ObjectId -> str для _id і user_id."""
    db = current_app.config['db']
    categories = list(db.event_categories.find({"user_id": user_id}))
    
    for cat in categories:
        cat['_id'] = str(cat['_id'])
        if 'user_id' in cat:
            try:
                cat['user_id'] = str(cat['user_id'])
            except:
                pass
    return categories

def _safe_parse_dt(value):
    """Спробувати нормалізувати start_time: якщо рядок у ISO -> datetime, якщо вже datetime -> повернути, інакше None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # пробуємо кілька форматів
        try:
            # Python ISO (може кидати ValueError)
            return datetime.fromisoformat(value)
        except Exception:
            # спробуємо YYYY-MM-DD HH:MM або YYYY-MM-DD
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(value, fmt)
                except Exception:
                    continue
    return None

# ------------------ Calendar view ------------------
@planner_bp.route('/calendar')
def calendar_view():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    db = current_app.config['db']
    try:
        user_id = ObjectId(session['user_id'])
    except Exception:
        # якщо session['user_id'] не валідний ObjectId
        return redirect(url_for('auth.login'))

    # Переконуємось, що у користувача є категорії
    ensure_user_categories(user_id)

    # отримуємо місяць/рік (за замовчуванням поточні)
    month = int(request.args.get('month', datetime.today().month))
    year = int(request.args.get('year', datetime.today().year))

    # границі місяця (timezone-naive)
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Отримуємо події в інтервалі (припускаємо, що start_time у БД — datetime)
    # Якщо в БД є якісь старі події як рядки, ми їх нормалізуємо після вибірки
    events_cursor = db.events.find({
        "user_id": user_id,
        "start_time": {"$gte": start_date, "$lt": end_date}
    })
    events = list(events_cursor)
    # DEBUG
    print(f"DEBUG: Found {len(events)} events for {month}/{year}")

    # Отримуємо категорії для підстановки
    categories_dict = {}
    for cat in db.event_categories.find({"user_id": user_id}):
        categories_dict[str(cat['_id'])] = cat

    # Обробляємо події: нормалізуємо start_time, додаємо time, category, created_at/updated_at
    for e in events:
        # normalize start_time
        st = _safe_parse_dt(e.get('start_time'))
        if st is None:
            # Якщо не вдалось спарсити start_time, ставимо created_at як fallback і пропускаємо час
            st = e.get('start_time') if isinstance(e.get('start_time'), datetime) else None

        e['start_time'] = st

        e['description'] = e.get('description', '')
        e['is_completed'] = e.get('is_completed', False)

        # created_at / updated_at: якщо збережені як рядки — намагаємось парсити, інакше fallback у now
        ca = e.get('created_at')
        ua = e.get('updated_at')
        e['created_at'] = _safe_parse_dt(ca) if ca else (st or datetime.utcnow())
        e['updated_at'] = _safe_parse_dt(ua) if ua else e['created_at']

        # time — використовуємо start_time, якщо він є
        if e.get('start_time'):
            try:
                e['time'] = e['start_time'].strftime("%H:%M")
            except Exception:
                e['time'] = None
        else:
            # якщо немає start_time, залишаємо старе поле time або None
            e['time'] = e.get('time')

        # category: нормалізуємо ObjectId -> str перед пошуком
        category_id = e.get('category_id')
        if isinstance(category_id, ObjectId):
            category_key = str(category_id)
        else:
            category_key = str(category_id) if category_id is not None else None

        if category_key and category_key in categories_dict:
            cat = categories_dict[category_key]
            e['category'] = {
                'name': cat.get('name_ua', ''),
                'icon': cat.get('icon', '📌'),
                'color': cat.get('color_hex', '#666666')
            }
        else:
            e['category'] = None

    month_names = ['', 'Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
                   'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень']
    month_name = month_names[month]

    # Правильно отримуємо перший день тижня (0 = понеділок)
    first_weekday, num_days = calendar.monthrange(year, month)
    today = datetime.today().date()

    days = []
    # Зручна мапа: ключ = 'YYYY-MM-DD' -> список подій того дня
    events_by_date = {}
    for e in events:
        st = e.get('start_time')
        if not st:
            continue
        date_key = st.strftime("%Y-%m-%d")
        events_by_date.setdefault(date_key, []).append(e)

    for day_num in range(1, num_days + 1):
        day_date = datetime(year, month, day_num)
        date_str = day_date.strftime("%Y-%m-%d")

        # безпечна фільтрація: беремо з events_by_date
        day_events = events_by_date.get(date_str, [])

        print(f"DEBUG: Day {day_num} ({date_str}): {len(day_events)} tasks")

        day_data = db.day_data.find_one({"user_id": user_id, "date": date_str})
        stickers = day_data.get('stickers', []) if day_data else []

        tasks = []
        for e in day_events:
            tasks.append({
                "_id": str(e.get("_id")),
                "title": e.get("title", ""),
                "description": e.get("description", ""),
                "time": e.get("time"),
                "is_completed": e.get("is_completed", False),
                "category": e.get("category"),
                "created_at": e.get("created_at"),
                "updated_at": e.get("updated_at"),
            })

        days.append({
            "date": date_str,
            "day_number": day_num,
            "stickers": stickers,
            "tasks_count": len(day_events),
            "is_today": day_date.date() == today,
            "tasks": tasks
        })

    # Будуємо тижні (понеділок = 0, неділя = 6)
    weeks = []
    week = []

    # Додаємо порожні клітинки перед першим днем місяця
    for _ in range(first_weekday):
        week.append(None)

    # Додаємо дні місяця
    for day in days:
        week.append(day)
        if len(week) == 7:
            weeks.append(week)
            week = []

    # Заповнюємо останній тиждень
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    # Отримуємо категорії для передачі в шаблон
    user_categories = get_user_categories(user_id)

    print(f"DEBUG: Total weeks: {len(weeks)}, Total categories: {len(user_categories)}")

    return render_template(
        'calendar.html',
        weeks=weeks,
        current_month_name=month_name,
        current_month=month,
        current_year=year,
        available_stickers=AVAILABLE_STICKERS,
        categories=user_categories
    )

# ------------------ Add task ------------------
@planner_bp.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    date = data.get('date')  # expected "YYYY-MM-DD"
    time = data.get('time')  # expected "HH:MM" or None
    category_id = data.get('category_id')

    print(f"DEBUG add_task: title={title}, date={date}, time={time}, category_id={category_id}")

    if not title or not date:
        return jsonify({"error": "Missing data (title/date)"}), 400

    db = current_app.config['db']
    try:
        user_id = ObjectId(session['user_id'])
    except Exception:
        return jsonify({"error": "Invalid session"}), 401

    # Гарантуємо що ми збудуємо datetime (варіант A)
    try:
        start_dt = build_datetime_from(date, time)
    except Exception as e:
        print(f"ERROR add_task: build_datetime_from failed: {e}")
        return jsonify({"error": "Invalid date/time format"}), 400

    now = datetime.utcnow()

    doc = {
        "user_id": user_id,
        "title": title,
        "description": description,
        "time": time,
        "start_time": start_dt,
        "end_time": start_dt,
        "is_completed": False,
        "created_at": now,
        "updated_at": now
    }
    
    # Додаємо category_id якщо вказано
    if category_id:
        try:
            doc["category_id"] = ObjectId(category_id)
        except Exception:
            # якщо не валідний ObjectId — ігноруємо (щоб не руйнувати запис)
            doc["category_id"] = None

    result = db.events.insert_one(doc)
    print(f"DEBUG: Task created with ID: {result.inserted_id}")

    # Оновлюємо статистику користувача
    db.users.update_one(
        {"_id": user_id},
        {"$inc": {"total_tasks": 1}},
        upsert=True
    )

    return jsonify({"success": True, "task_id": str(result.inserted_id)})

# ------------------ Get tasks for date ------------------
# У файлі routes/planner.py замініть функцію get_tasks

@planner_bp.route('/get_tasks/<date>')
def get_tasks(date):
    if 'user_id' not in session:
        print("ERROR: No user_id in session")
        return jsonify([])

    db = current_app.config['db']
    try:
        user_id = ObjectId(session['user_id'])
    except Exception:
        print("ERROR: Invalid session user_id")
        return jsonify([])

    print(f"DEBUG get_tasks: user_id={user_id}, date={date}")
    
    # FIX: створюємо правильний datetime-діапазон на цілий день (UTC)
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
    except ValueError as e:
        print(f"ERROR: Invalid date format: {date}, error: {e}")
        return jsonify({"error": "Invalid date format"}), 400

    next_day = target_date + timedelta(days=1)
    
    print(f"DEBUG get_tasks: Searching between {target_date} and {next_day}")

    # FIX: фільтр на start_time (datetime) - важливо порівнювати datetime об'єкти!
    try:
        tasks = list(db.events.find({
            "user_id": user_id,
            "start_time": {
                "$gte": target_date,
                "$lt": next_day
            }
        }).sort("start_time", 1))
    except Exception as e:
        print(f"ERROR in database query: {e}")
        return jsonify({"error": "Database error"}), 500

    print(f"DEBUG get_tasks: Found {len(tasks)} tasks")

    # Отримуємо категорії
    categories_dict = {}
    try:
        for c in db.event_categories.find({"user_id": user_id}):
            categories_dict[str(c['_id'])] = c
    except Exception as e:
        print(f"ERROR loading categories: {e}")

    out = []
    for t in tasks:
        # Нормалізуємо start_time - це вже має бути datetime від MongoDB
        st = t.get('start_time')
        if isinstance(st, datetime):
            st_parsed = st
        else:
            st_parsed = _safe_parse_dt(st)
        
        created = _safe_parse_dt(t.get('created_at'))
        updated = _safe_parse_dt(t.get('updated_at'))

        # Якщо start_time не існує, пропускаємо це завдання
        if not st_parsed:
            print(f"WARNING: Task {t.get('_id')} has no valid start_time, skipping")
            continue

        category_id = t.get('category_id')
        category_info = None
        if category_id:
            category_key = str(category_id)
            if category_key in categories_dict:
                cat = categories_dict[category_key]
                category_info = {
                    'id': str(cat['_id']),
                    'name': cat.get('name_ua', ''),
                    'icon': cat.get('icon', '📌'),
                    'color': cat.get('color_hex', '#666666')
                }
        
        # Якщо немає time в окремому полі, беремо з start_time
        task_time = t.get("time")
        if not task_time and st_parsed:
            try:
                task_time = st_parsed.strftime("%H:%M")
            except Exception:
                task_time = None
        
        task_data = {
            "_id": str(t.get("_id")),
            "title": t.get("title", ""),
            "description": t.get("description", ""),
            "time": task_time,
            "is_completed": t.get("is_completed", False),
            "category": category_info,
            "created_at": created.isoformat() if created else None,
            "updated_at": updated.isoformat() if updated else None
        }
        
        print(f"DEBUG: Returning task: {task_data['title']}, time: {task_data['time']}, start_time: {st_parsed}")
        out.append(task_data)

    print(f"DEBUG get_tasks: Returning {len(out)} tasks as JSON")
    return jsonify(out)

# ------------------ Edit task ------------------
@planner_bp.route('/edit_task/<task_id>', methods=['POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    db = current_app.config['db']
    
    try:
        task = db.events.find_one({"_id": ObjectId(task_id)})
    except Exception:
        return jsonify({"error": "Invalid task id"}), 400

    if not task:
        return jsonify({"error": "Task not found"}), 404

    update = {}
    if 'title' in data:
        update['title'] = data['title'].strip()
    if 'description' in data:
        update['description'] = data['description'].strip()
    if 'time' in data:
        update['time'] = data['time']  # зберігаємо копію рядка
    if 'category_id' in data:
        if data['category_id']:
            try:
                update['category_id'] = ObjectId(data['category_id'])
            except Exception:
                update['category_id'] = None
        else:
            update['category_id'] = None
    
    if 'date' in data:
        # будуємо новий start_time з date + (time якщо є)
        new_time = data.get('time') or task.get('time')
        try:
            start_dt = build_datetime_from(data['date'], new_time)
            update['start_time'] = start_dt
            update['end_time'] = start_dt
            # якщо є час — зберігаємо і в поле time
            if new_time:
                update['time'] = new_time
        except Exception as e:
            print(f"ERROR edit_task: invalid date/time: {e}")
            return jsonify({"error": "Invalid date/time"}), 400

    if update:
        update['updated_at'] = datetime.utcnow()
        db.events.update_one({"_id": ObjectId(task_id)}, {"$set": update})
        print(f"DEBUG: Task {task_id} updated with: {update}")

    return jsonify({"success": True})

# ------------------ Toggle task completed ------------------
@planner_bp.route('/toggle_task/<task_id>', methods=['POST'])
def toggle_task(task_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db = current_app.config['db']
    try:
        user_id = ObjectId(session['user_id'])
    except Exception:
        return jsonify({"error": "Invalid session"}), 401

    try:
        task = db.events.find_one({"_id": ObjectId(task_id)})
    except Exception:
        return jsonify({"error": "Invalid task id"}), 400
    
    if not task:
        return jsonify({"error": "Task not found"}), 404

    new_state = not task.get('is_completed', False)
    db.events.update_one(
        {"_id": ObjectId(task_id)}, 
        {"$set": {"is_completed": new_state, "updated_at": datetime.utcnow()}}
    )
    
    # Оновлюємо статистику
    if new_state:
        db.users.update_one({"_id": user_id}, {"$inc": {"completed_tasks": 1}}, upsert=True)
    else:
        db.users.update_one({"_id": user_id}, {"$inc": {"completed_tasks": -1}}, upsert=True)

    print(f"DEBUG: Task {task_id} toggled to {new_state}")

    return jsonify({"success": True, "is_completed": new_state})

# ------------------ Delete task ------------------
@planner_bp.route('/delete_task/<task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    db = current_app.config['db']
    try:
        result = db.events.delete_one({"_id": ObjectId(task_id)})
    except Exception:
        return jsonify({"error": "Invalid task id"}), 400
    
    if result.deleted_count > 0:
        print(f"DEBUG: Task {task_id} deleted")
        return jsonify({"success": True})
    return jsonify({"error": "Task not found"}), 404

# ------------------ Categories Management ------------------
@planner_bp.route('/get_categories')
def get_categories():
    if 'user_id' not in session:
        return jsonify([])
    
    try:
        user_id = ObjectId(session['user_id'])
    except Exception:
        return jsonify([])

    ensure_user_categories(user_id)
    categories = get_user_categories(user_id)
    
    return jsonify(categories)

@planner_bp.route('/add_category', methods=['POST'])
def add_category():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json() or {}
    name = (data.get('name_ua') or '').strip()
    icon = data.get('icon', '📌')
    color = data.get('color_hex', '#666666')
    
    if not name:
        return jsonify({"error": "Name required"}), 400
    
    db = current_app.config['db']
    try:
        user_id = ObjectId(session['user_id'])
    except Exception:
        return jsonify({"error": "Invalid session"}), 401
    
    result = db.event_categories.insert_one({
        "user_id": user_id,
        "name_ua": name,
        "icon": icon,
        "color_hex": color,
        "created_at": datetime.utcnow()
    })
    
    return jsonify({"success": True, "id": str(result.inserted_id)})

# ------------------ Add/Get stickers ------------------
@planner_bp.route('/add_sticker', methods=['POST'])
def add_sticker():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    date = data.get('date')
    sticker = data.get('sticker')

    if not date or not sticker:
        return jsonify({"error": "Missing data"}), 400

    db = current_app.config['db']
    try:
        user_id = ObjectId(session['user_id'])
    except Exception:
        return jsonify({"error": "Invalid session"}), 401

    day_data = db.day_data.find_one({"user_id": user_id, "date": date})
    current_stickers = day_data.get('stickers', []) if day_data else []

    if len(current_stickers) >= 10:
        return jsonify({"error": "Maximum stickers reached"}), 400

    db.day_data.update_one(
        {"user_id": user_id, "date": date},
        {"$addToSet": {"stickers": sticker}},
        upsert=True
    )
    return jsonify({"success": True})

@planner_bp.route('/get_stickers/<date>')
def get_stickers(date):
    if 'user_id' not in session:
        return jsonify([])

    db = current_app.config['db']
    try:
        user_id = ObjectId(session['user_id'])
    except Exception:
        return jsonify([])

    day_data = db.day_data.find_one({"user_id": user_id, "date": date})
    stickers = day_data.get('stickers', []) if day_data else []
    return jsonify(stickers)