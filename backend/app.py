from flask import Flask, render_template, session
from flask_pymongo import PyMongo
from backend.config import MONGO_URI, SECRET_KEY

from backend.routes.auth import auth_bp
from backend.routes.planner import planner_bp

app = Flask(__name__)

# Налаштування
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MONGO_URI'] = MONGO_URI

# Ініціалізація Mongo
try:
    mongo = PyMongo(app)
    app.config['db'] = mongo.db
    print("✓ MongoDB configured successfully")
except Exception as e:
    print(f"✗ MongoDB configuration error: {e}")
    mongo = None

# Реєстрація blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(planner_bp)

# Головна сторінка
@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('calendar.html')
    return render_template('index.html')

# Здоров'я check endpoint
@app.route('/health')
def health():
    try:
        if mongo and app.config.get('db'):
            app.config['db'].command('ping')
            return {'status': 'healthy', 'db': 'connected'}, 200
        else:
            return {'status': 'unhealthy', 'db': 'not_initialized'}, 500
    except Exception as e:
        print(f"Health check error: {e}")
        return {'status': 'unhealthy', 'error': str(e)}, 500

# Обробка 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)