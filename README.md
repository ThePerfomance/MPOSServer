# МПОС — Сервер мобильной обучающей системы

Бэкенд для мобильного приложения **«Обучающая система с персонализацией образовательного контента»**.  
Написан на Python + Django, использует PostgreSQL и ML-алгоритмы для кластеризации студентов, сегментации тестов и прогнозирования результатов.

---

## Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.12 |
| Фреймворк | Django 5 + Django REST Framework |
| База данных | PostgreSQL 16 |
| ML | scikit-learn (KMeans, LinearRegression) |
| Контейнеризация | Docker + Docker Compose |

---

## Быстрый старт

### Требования
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (запущен)

### Запуск
```bash
docker compose up --build
```

При первом запуске автоматически:
1. Поднимается PostgreSQL
2. Применяются миграции
3. БД заполняется тестовыми данными (`seed_db`)
4. Сервер стартует на `http://localhost:8000`

### Остановка
```bash
docker compose down
```

### Сброс БД (полная очистка)
```bash
docker compose down -v
docker compose up --build
```

---

## Структура проекта

```
MPOSServer/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
├── config/
│   ├── settings.py       # Настройки Django
│   └── urls.py           # Корневые маршруты
├── api/
│   ├── models.py         # Модели БД
│   ├── serializers.py    # DRF сериализаторы
│   ├── views.py          # Обработчики запросов
│   ├── urls.py           # Маршруты API
│   └── management/
│       └── commands/
│           └── seed_db.py  # Команда заполнения БД
└── ml/
    └── engine.py         # ML-алгоритмы
```

---

## API — Основные эндпоинты

### Пользователи
| Метод | URL | Описание |
|-------|-----|----------|
| GET, POST | `/users` | Список / создать |
| GET, PUT, DELETE | `/users/<uuid>` | CRUD |
| GET | `/users/by-email/<email>` | Поиск по email |
| GET | `/users/<uuid>/groups` | Группы пользователя |
| GET | `/users/<uuid>/results` | Результаты тестов |

### Группы
| Метод | URL | Описание |
|-------|-----|----------|
| GET, POST | `/groups` | Список / создать |
| GET, PUT, DELETE | `/groups/<uuid>` | CRUD |
| GET | `/groups/by-name/<name>` | Поиск по имени |
| GET | `/groups/<uuid>/users` | Студенты в группе |

### Участники групп
| Метод | URL | Описание |
|-------|-----|----------|
| GET, POST | `/group-members` | Список / добавить |
| GET, PUT, DELETE | `/group-members/<uuid>` | CRUD |

### Дисциплины
| Метод | URL | Описание |
|-------|-----|----------|
| GET, POST | `/subjects` | Список / создать |
| GET, PUT, DELETE | `/subjects/<uuid>` | CRUD |
| GET | `/subjects/by-name/<name>` | Поиск по имени |

### Тесты
| Метод | URL | Описание |
|-------|-----|----------|
| GET, POST | `/tests` | Список / создать |
| GET, PUT, DELETE | `/tests/<id>` | CRUD |
| GET | `/tests/<id>/questions` | Вопросы с ответами |

### Результаты тестов
| Метод | URL | Описание |
|-------|-----|----------|
| GET, POST | `/test-results` | Список / создать |
| GET, PUT, DELETE | `/test-results/<uuid>` | CRUD |

### Вопросы и ответы
| Метод | URL | Описание |
|-------|-----|----------|
| GET, POST | `/questions` | Список / создать |
| GET, PUT, DELETE | `/questions/<id>` | CRUD |
| GET, POST | `/answers` | Список / создать |
| GET, PUT, DELETE | `/answers/<id>` | CRUD |

---

## ML-эндпоинты

### Порядок вызова
```
1. POST /ml/cluster-students   ← сначала кластеризовать студентов
2. POST /ml/segment-tests      ← затем сегментировать тесты
3. GET  /ml/recommendations/<user_id>  ← потом получить рекомендации
```

### Описание

| Метод | URL | Алгоритм | Описание |
|-------|-----|----------|----------|
| POST | `/ml/cluster-students` | KMeans | Разбивает студентов на кластеры: **слабый / средний / сильный** |
| POST | `/ml/segment-tests` | Percentile | Присваивает тестам уровень: **easy / medium / hard** |
| POST | `/ml/predict-result` | LinearRegression | Прогнозирует балл студента для теста |
| GET | `/ml/recommendations/<uuid>` | Rule-based | Персональные рекомендации по обучению |
| GET | `/ml/clusters/<uuid>` | — | Кластер конкретного студента |
| GET | `/ml/test-difficulty/<id>` | — | Сложность конкретного теста |

### Примеры запросов (PowerShell)

**Кластеризация студентов:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/ml/cluster-students" `
  -Method POST -ContentType "application/json" -Body '{}'
```

**Сегментация тестов:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/ml/segment-tests" `
  -Method POST -ContentType "application/json" -Body '{}'
```

**Прогноз результата:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/ml/predict-result" `
  -Method POST -ContentType "application/json" `
  -Body '{"user_id": "<uuid студента>", "test_id": 1}'
```

**Рекомендации для студента:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/ml/recommendations/<uuid студента>"
```

### Примеры запросов (curl)

```bash
# Кластеризация
curl -X POST http://localhost:8000/ml/cluster-students

# Рекомендации
curl http://localhost:8000/ml/recommendations/<user_uuid>
```

---

## База данных

### Основные таблицы (порт с Rust-сервера)

| Таблица | Описание |
|---------|----------|
| `users` | Пользователи (студенты и преподаватели) |
| `groups` | Учебные группы |
| `group_members` | Связь студентов и групп |
| `subjects` | Учебные дисциплины |
| `tests` | Тесты |
| `questions` | Вопросы |
| `answers` | Варианты ответов |
| `test_results` | Результаты прохождения тестов |

### ML-таблицы (новые)

| Таблица | Описание |
|---------|----------|
| `student_clusters` | Кластер каждого студента и его метка |
| `test_difficulties` | Уровень сложности каждого теста |
| `score_predictions` | Прогнозируемые баллы (студент × тест) |
| `recommendations` | Персональные рекомендации по обучению |

---

## Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `DATABASE_URL` | `postgres://eduuser:edupassword@db:5432/edudb` | Строка подключения к БД |
| `DJANGO_SECRET_KEY` | `django-insecure-dev-key` | Секретный ключ Django |
| `DEBUG` | `True` | Режим отладки |
