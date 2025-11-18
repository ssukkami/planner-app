# backend/app.py
from flask import Flask, render_template, session
from flask_pymongo import PyMongo
from backend.config import MONGO_URI, SECRET_KEY

from backend.routes.auth import auth_bp
from backend.routes.planner import planner_bp
# from routes.ai import ai_bp  # якщо буде AI маршрут

app = Flask(__name__)

# Налаштування
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MONGO_URI'] = MONGO_URI

# Ініціалізація Mongo
mongo = PyMongo(app)
app.config['db'] = mongo.db  # робимо доступною базу через current_app.config['db']

# Реєстрація blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(planner_bp)
# app.register_blueprint(ai_bp, url_prefix='/ai')  # якщо AI потрібен

# Головна сторінка
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('calendar.html')
    return render_template('index.html')

# Обробка 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)
