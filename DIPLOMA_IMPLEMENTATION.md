# Реализация темы диплома "Мобильное приложение обучающей системы с персонализацией контента"

## 📚 Описание решения

Данная реализация полностью меняет подход к персонализации в обучающей системе:

### ❌ Старый подход (удалён):
- Кластеризация студентов через KMeans (5 признаков)
- Сегментация тестов по сложности (easy/medium/hard)
- Rule-based рекомендации на основе матрицы (rank × difficulty)
- Прогнозирование результатов через Linear Regression

### ✅ Новый подход (для диплома):
- **Анализ каждого ответа пользователя** на уровне вопроса
- **Определение слабых тем** на основе процента ошибок
- **Персонализированные рекомендации** с ссылками на материалы
- **Индивидуальная траектория обучения** (study → watch → practice)

---

## 🔧 Новые ML-алгоритмы

### 1. `analyze_weak_topics()` — Анализ слабых тем

**Файл:** `ml/engine.py`

**Алгоритм:**
```python
def analyze_weak_topics(user_answers: list[dict], questions_map: dict) -> dict:
    """
    Анализирует ответы пользователя и определяет слабые темы.
    
    Для каждой темы вычисляется:
    - error_rate = incorrect / (correct + incorrect)
    - Тема считается слабой, если error_rate > 0.3 (30% ошибок)
    """
```

**Входные данные:**
- `user_answers`: список ответов пользователя
  ```json
  [
    {
      "question_id": 123,
      "is_correct": false,
      "answered_at": "2024-01-15T10:30:00Z",
      "test_id": 5
    }
  ]
  ```
- `questions_map`: информация о вопросах
  ```json
  {
    "123": {
      "topic": "Линейная алгебра",
      "block_id": "...",
      "lesson_id": "...",
      "recommendation_link": "https://...",
      "recommendation_video_link": "https://..."
    }
  }
  ```

**Выходные данные:**
```json
{
  "weak_topics": [
    {
      "topic": "Линейная алгебра",
      "error_rate": 0.75,
      "error_count": 6,
      "total_attempts": 8,
      "last_error_at": "2024-01-15T10:30:00Z"
    }
  ],
  "topic_details": {
    "Линейная алгебра": {
      "questions": [123, 124, ...],
      "resources": ["https://..."],
      "accuracy": 0.25
    }
  },
  "overall_stats": {
    "total_questions": 50,
    "correct": 35,
    "accuracy": 0.7
  }
}
```

---

### 2. `generate_personalized_recommendations()` — Генерация рекомендаций

**Алгоритм:**
```python
def generate_personalized_recommendations(
    weak_topics_analysis: dict,
    lessons_map: dict,
    videos_map: dict,
    blocks_map: dict
) -> list[dict]:
    """
    Генерирует персонализированные рекомендации.
    
    Приоритет вычисляется как:
    priority = min(10, max(1, int(error_rate * 10) + (error_count // 3)))
    """
```

**Тексты рекомендаций:**
| error_rate | Текст рекомендации |
|------------|-------------------|
| ≥ 0.7 | "Критическая проблема по теме '{topic}'. Необходимо срочно повторить материал." |
| ≥ 0.5 | "Рекомендуется повторить тему '{topic}' — высокий процент ошибок." |
| ≥ 0.3 | "Стоит обратить внимание на тему '{topic}' для улучшения результатов." |

**Ресурсы подбираются автоматически:**
1. Конспекты уроков (по matching названия темы и урока)
2. Видео (если есть привязка к уроку)
3. Внешние ссылки из вопросов (`recommendation_link`, `recommendation_video_link`)

**Выходные данные:**
```json
[
  {
    "topic": "Линейная алгебра",
    "priority": 9,
    "recommendation_text": "Критическая проблема по теме 'Линейная алгебра'...",
    "resources": [
      {
        "type": "lesson",
        "title": "Конспект: Основы линейной алгебры",
        "url": "/lessons/uuid/",
        "content": "Краткое содержание..."
      },
      {
        "type": "video",
        "title": "Видео: Лекция по линейной алгебре",
        "url": "https://rutube.ru/..."
      },
      {
        "type": "link",
        "title": "Материал для повторения",
        "url": "https://..."
      }
    ],
    "practice_questions": [123, 124, 125],
    "error_rate": 0.75,
    "error_count": 6
  }
]
```

---

### 3. `analyze_progress_over_time()` — Анализ прогресса

**Алгоритм:**
```python
def analyze_progress_over_time(user_answers: list[dict], window_days: int = 7) -> dict:
    """
    Анализирует прогресс пользователя по времени.
    
    Разбивает ответы на периоды (по 7 дней) и вычисляет:
    - accuracy для каждого периода
    - тренд: improving / declining / stable
    """
```

**Определение тренда:**
```python
diff = recent_accuracy - previous_accuracy

if diff > 0.1:
    trend = "improving"
elif diff < -0.1:
    trend = "declining"
else:
    trend = "stable"
```

**Выходные данные:**
```json
{
  "trend": "improving",
  "periods": [
    {
      "period": "2024-01-01 to 2024-01-07",
      "accuracy": 0.65,
      "questions": 20
    },
    {
      "period": "2024-01-08 to 2024-01-14",
      "accuracy": 0.78,
      "questions": 25
    }
  ],
  "recommendation": "Отличный прогресс! Продолжайте в том же духе."
}
```

---

### 4. `build_learning_path()` — Индивидуальная траектория

**Алгоритм:**
```python
def build_learning_path(
    weak_topics_analysis: dict,
    recommendations: list[dict],
    blocks_structure: dict
) -> list[dict]:
    """
    Строит пошаговую траекторию обучения.
    
    Для каждой рекомендации создаёт шаги:
    1. study — изучение теории (конспект)
    2. watch — просмотр видео
    3. practice — практика на вопросах
    """
```

**Выходные данные:**
```json
[
  {
    "step": 1,
    "action": "study",
    "topic": "Линейная алгебра",
    "resource": {
      "type": "lesson",
      "title": "Конспект: Основы линейной алгебры",
      "url": "/lessons/uuid/"
    },
    "estimated_time_minutes": 15
  },
  {
    "step": 2,
    "action": "watch",
    "topic": "Линейная алгебра",
    "resource": {
      "type": "video",
      "title": "Видео: Лекция по линейной алгебре",
      "url": "https://..."
    },
    "estimated_time_minutes": 10
  },
  {
    "step": 3,
    "action": "practice",
    "topic": "Линейная алгебра",
    "question_ids": [123, 124, 125],
    "estimated_time_minutes": 20
  }
]
```

---

## 🌐 API Endpoints

### 1. `POST /api/ml/analyze-weak-topics/<user_id>/`

**Описание:** Анализирует ответы пользователя и определяет слабые темы.

**Request Body (опционально):**
```json
{
  "limit_days": 30
}
```

**Response:**
```json
{
  "weak_topics": [...],
  "topic_details": {...},
  "overall_stats": {...}
}
```

**Пример использования (Kotlin/Android):**
```kotlin
suspend fun analyzeWeakTopics(userId: String, limitDays: Int? = null) {
    val body = limitDays?.let { mapOf("limit_days" to it) } ?: emptyMap()
    
    val response = apiService.post(
        "/ml/analyze-weak-topics/$userId/",
        body
    )
    
    displayWeakTopics(response.weak_topics)
}
```

---

### 2. `GET /api/ml/personalized-recommendations/<user_id>/`

**Описание:** Генерирует персонализированные рекомендации с ссылками на материалы.

**Query Parameters:**
- `limit_days` (опционально): анализировать ответы за последние N дней
- `max_recommendations` (опционально): максимальное количество рекомендаций (по умолчанию 10)

**Пример запроса:**
```
GET /api/ml/personalized-recommendations/550e8400-e29b-41d4-a716-446655440000/?limit_days=30&max_recommendations=5
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "recommendations": [
    {
      "topic": "Линейная алгебра",
      "priority": 9,
      "recommendation_text": "Критическая проблема...",
      "resources": [...],
      "practice_questions": [123, 124, 125],
      "error_rate": 0.75,
      "error_count": 6
    }
  ],
  "overall_stats": {
    "total_questions": 50,
    "correct": 35,
    "accuracy": 0.7
  },
  "progress_analysis": {
    "trend": "improving",
    "periods": [...],
    "recommendation": "Отличный прогресс!..."
  }
}
```

**Пример использования (Kotlin/Android):**
```kotlin
suspend fun getPersonalizedRecommendations(
    userId: String,
    limitDays: Int? = 30,
    maxRecs: Int = 5
) {
    val response = apiService.get(
        "/ml/personalized-recommendations/$userId/",
        params = mapOf(
            "limit_days" to limitDays.toString(),
            "max_recommendations" to maxRecs.toString()
        )
    )
    
    showRecommendations(response.recommendations)
    showProgressTrend(response.progress_analysis.trend)
}
```

---

### 3. `GET /api/ml/learning-path/<user_id>/`

**Описание:** Строит индивидуальную траекторию обучения.

**Query Parameters:**
- `limit_days` (опционально): анализировать ответы за последние N дней
- `max_steps` (опционально): максимальное количество шагов (по умолчанию 5)

**Пример запроса:**
```
GET /api/ml/learning-path/550e8400-e29b-41d4-a716-446655440000/?limit_days=30&max_steps=5
```

**Response:**
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "learning_path": [
    {
      "step": 1,
      "action": "study",
      "topic": "Линейная алгебра",
      "resource": {...},
      "estimated_time_minutes": 15
    },
    ...
  ],
  "total_estimated_time_minutes": 45
}
```

**Пример использования (Kotlin/Android):**
```kotlin
suspend fun getLearningPath(userId: String, maxSteps: Int = 5) {
    val response = apiService.get(
        "/ml/learning-path/$userId/",
        params = mapOf("max_steps" to maxSteps.toString())
    )
    
    renderLearningPath(response.learning_path)
    showTotalTime(response.total_estimated_time_minutes)
}
```

---

## 📊 Научная новизна для диплома

### 1. Переход от кластеризации к индивидуальному анализу

**Было:**
- Студенты группируются в кластеры (S/A/B/C/D)
- Рекомендации одинаковы для всех студентов одного кластера
- Игнорируются индивидуальные пробелы в знаниях

**Стало:**
- Анализ каждого ответа конкретного студента
- Уникальные рекомендации для каждого пользователя
- Точное определение проблемных тем

---

### 2. Многофакторная оценка слабых тем

**Формула приоритета:**
```
priority = min(10, max(1, int(error_rate * 10) + (error_count // 3)))
```

**Факторы:**
1. **error_rate** — процент ошибок по теме (0.0–1.0)
2. **error_count** — абсолютное количество ошибок
3. **recency** — время последней ошибки (через `last_error_at`)

---

### 3. Автоматический подбор ресурсов

**Алгоритм matching:**
```python
def _topic_matches(title: str, summary: str, topic: str) -> bool:
    text = f"{title} {summary}".lower()
    topic_lower = topic.lower()
    
    # Прямое вхождение
    if topic_lower in text:
        return True
    
    # Частичное совпадение (для составных тем)
    topic_words = topic_lower.split()
    if len(topic_words) > 1:
        matches = sum(1 for word in topic_words if word in text)
        if matches >= len(topic_words) // 2 + 1:
            return True
    
    return False
```

---

### 4. Динамическая траектория обучения

**Структура шагов:**
```
study (конспект) → watch (видео) → practice (вопросы)
```

**Оценка времени:**
- study: 15 минут
- watch: 10 минут
- practice: 20 минут

---

## 🧪 Эксперименты для диплома

### Эксперимент 1: Сравнение качества рекомендаций

**Группы:**
- **Группа A (control)**: старые rule-based рекомендации
- **Группа B (treatment)**: новые персонализированные рекомендации

**Метрики:**
1. % завершённых рекомендованных материалов
2. Среднее время обучения в неделю
3. Улучшение результатов тестов (Δ accuracy)

**Ожидаемый результат:** Группа B покажет улучшение на 20-30%

---

### Эксперимент 2: Точность определения слабых тем

**Методология:**
1. Собрать ответы 50 студентов за семестр
2. Попросить преподавателей вручную определить слабые темы
3. Сравнить с результатами алгоритма

**Метрика:**
```
precision = TP / (TP + FP)
recall = TP / (TP + FN)
F1 = 2 * (precision * recall) / (precision + recall)
```

**Ожидаемый результат:** F1-score ≥ 0.75

---

### Эксперимент 3: Влияние на успеваемость

**Дизайн:**
- Измерить accuracy студентов до внедрения системы
- Измерить accuracy после 4 недель использования
- Вычислить Δ accuracy

**Гипотеза:** 
```
H0: Δ accuracy = 0
H1: Δ accuracy > 0
```

**Ожидаемый результат:** p-value < 0.05, Δ accuracy ≈ 10-15%

---

## 📈 Визуализация для защиты

### График 1: Распределение слабых тем

```python
import matplotlib.pyplot as plt

topics = [t["topic"] for t in weak_topics]
error_rates = [t["error_rate"] for t in weak_topics]

plt.barh(topics, error_rates, color='coral')
plt.xlabel('Процент ошибок')
plt.title('Слабые темы студента')
plt.xlim(0, 1)
plt.show()
```

### График 2: Прогресс по времени

```python
periods = [p["period"] for p in progress["periods"]]
accuracies = [p["accuracy"] for p in progress["periods"]]

plt.plot(periods, accuracies, marker='o', linewidth=2)
plt.fill_between(periods, accuracies, alpha=0.3)
plt.xlabel('Период')
plt.ylabel('Точность (%)')
plt.title('Динамика успеваемости')
plt.xticks(rotation=45)
plt.show()
```

### График 3: Структура рекомендаций

```python
types = ['lesson', 'video', 'link']
counts = [
    sum(1 for r in recs for res in r["resources"] if res["type"] == 'lesson'),
    sum(1 for r in recs for res in r["resources"] if res["type"] == 'video'),
    sum(1 for r in recs for res in r["resources"] if res["type"] == 'link')
]

plt.pie(counts, labels=types, autopct='%1.1f%%')
plt.title('Типы рекомендованных ресурсов')
plt.show()
```

---

## 🎯 Пример сценария использования

### Сценарий: Студент Иван проходит тест по математике

**1. Иван регистрируется в системе**
```
POST /api/users/
{
  "email": "ivan@student.ru",
  "firstname": "Иван",
  "lastname": "Иванов",
  "role": "student"
}
```

**2. Иван проходит тест**
```
POST /api/test-results/
{
  "user_id": "...",
  "test_id": 5,
  "score": 60,
  "started_at": "2024-01-15T10:00:00Z",
  "answers": [
    {"question_id": 123, "chosen_answer_id": 456, "is_correct": false},
    {"question_id": 124, "chosen_answer_id": 457, "is_correct": true},
    ...
  ]
}
```

**3. Система анализирует ошибки**
```
POST /api/ml/analyze-weak-topics/{ivan_id}/
→ Возвращает слабые темы
```

**4. Иван получает рекомендации**
```
GET /api/ml/personalized-recommendations/{ivan_id}/
→ Возвращает:
   - Тема: "Линейная алгебра" (priority: 9)
   - Ресурсы: конспект, видео, внешняя ссылка
   - Вопросы для практики: [123, 124, 125]
```

**5. Иван следует траектории**
```
GET /api/ml/learning-path/{ivan_id}/
→ Возвращает пошаговый план:
   Шаг 1: Изучить конспект (15 мин)
   Шаг 2: Посмотреть видео (10 мин)
   Шаг 3: Решить 5 вопросов (20 мин)
```

**6. Через неделю система оценивает прогресс**
```
GET /api/ml/personalized-recommendations/{ivan_id}/?limit_days=7
→ trend: "improving"
→ recommendation: "Отличный прогресс! Продолжайте в том же духе."
```

---

## 📝 Структура раздела диплома

### Глава 3: Реализация системы персонализации

**3.1. Архитектура ML-компонента**
- Схема взаимодействия: Mobile App ↔ API ↔ ML Engine ↔ Database
- Описание моделей данных (UserAnswer, Question, Lesson, Video)

**3.2. Алгоритм анализа слабых тем**
- Псевдокод функции `analyze_weak_topics()`
- Обоснование порога 30% ошибок
- Формула вычисления error_rate

**3.3. Генерация персонализированных рекомендаций**
- Алгоритм подбора ресурсов (matching тем)
- Формула приоритета
- Классификация типов ресурсов (lesson/video/link)

**3.4. Построение индивидуальной траектории**
- Модель шагов (study/watch/practice)
- Оценка времени выполнения
- Адаптивность к прогрессу студента

**3.5. Программная реализация**
- Листинг ключевых функций (`ml/engine.py`)
- Описание API endpoints (`api/views.py`, `api/urls.py`)
- Интеграция с мобильным приложением

**3.6. Экспериментальная оценка**
- Дизайн экспериментов
- Метрики качества
- Результаты и выводы

---

## ✅ Checklist для готовности диплома

- [x] Реализован ML-движок (`ml/engine.py`)
- [x] Созданы API endpoints (`api/views.py`, `api/urls.py`)
- [ ] Наполнена база тестовыми данными (seed_db)
- [ ] Проведены эксперименты (сбор метрик)
- [ ] Подготовлены визуализации (графики)
- [ ] Описана научная новизна в тексте диплома
- [ ] Интегрировано с мобильным приложением (вызовы API)

---

## 📞 Контакты для вопросов

Если возникнут вопросы по реализации:
1. Проверьте документацию API выше
2. Изучите код `ml/engine.py` — там подробные комментарии
3. Используйте эндпоинт `/ml/analyze-weak-topics/` для отладки

Удачи с защитой диплома! 🎓
