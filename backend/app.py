from flask import Flask, render_template, session
from flask_pymongo import PyMongo
from backend.config import MONGO_URI, SECRET_KEY
import ssl
import certifi

from backend.routes.auth import auth_bp
from backend.routes.planner import planner_bp

app = Flask(__name__)

# Налаштування
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MONGO_URI'] = MONGO_URI

# PyMongo конфіг для SSL/TLS на Render
app.config['MONGOCLIENT_KWARGS'] = {
    'ssl': True,
    'ssl_cert_reqs': 'CERT_NONE',
    'tlsAllowInvalidCertificates': True,
    'tlsCAFile': certifi.where(),
    'serverSelectionTimeoutMS': 5000,
    'connectTimeoutMS': 10000,
    'socketTimeoutMS': 10000,
    'retryWrites': True,
}

# Ініціалізація Mongo
mongo = PyMongo(app)
app.config['db'] = mongo.db

# Реєстрація blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(planner_bp)

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