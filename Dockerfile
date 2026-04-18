FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Убеждаемся что __init__.py файлы существуют
RUN touch api/management/__init__.py api/management/commands/__init__.py

EXPOSE 8000

