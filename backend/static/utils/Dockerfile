# Базовий образ
FROM python:3.10

# Робоча директорія всередині контейнера
WORKDIR /app

# Скопіювати файли проєкту до контейнера
COPY . .

# Встановити залежності
RUN pip install --no-cache-dir -r requirements.txt

# Вказати порт, який використовує Flask
EXPOSE 5000

# Запуск застосунку
CMD ["python", "app.py"]
