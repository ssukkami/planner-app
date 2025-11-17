from flask import Blueprint, render_template, request, session, redirect, url_for
import requests
from config import HF_API_KEY

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

@ai_bp.route('/', methods=['GET', 'POST'])
def mood():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    result = None
    if request.method == 'POST':
        text = request.form['text']
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        payload = {"inputs": text}
        response = requests.post(
            "https://api-inference.huggingface.co/models/distilbert-base-uncased-finetuned-sst-2-english",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            # Hugging Face повертає список, беремо перший результат
            result = response.json()[0][0]
    return render_template('mood.html', result=result)
