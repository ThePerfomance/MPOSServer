# Изменения в логике работы тренажёра

## 1. Разделение сессий по урокам

### Модель TrainingSession (api/models.py)
- Добавлено поле `lesson` (ForeignKey на Lesson, nullable)
- Сессии теперь группируются по комбинации `(user + lesson + status)`
- Добавлен индекс для быстрого поиска: `Index(fields=['user', 'lesson', 'status'])`

### Логика создания сессии (api/views.py - create_training_from_result)
- При создании сессии определяется урок через связь `Test -> Lesson`
- Поиск существующей активной сессии теперь учитывает lesson:
  ```python
  session_filters = {'user': test_result.user, 'status': 'active'}
  if lesson:
      session_filters['lesson'] = lesson
  ```
- Сессии для разных уроков больше не сливаются

## 2. Логика завершения при 4+ ответах из 10

В функции `create_training_from_result` добавлена проверка:

```python
# Если пользователь ответил на 4+ вопроса и всего вопросов >= 10
if answered_count >= 4 and total_questions >= 10:
    # Получаем неотвеченные вопросы
    pending_questions = session.training_questions.filter(status='pending')
    
    if pending_questions.count() > 0:
        # Создаём новую сессию для оставшихся вопросов
        new_session = TrainingSession.objects.create(...)
        
        # Переносим неотвеченные вопросы
        for tq in pending_questions:
            TrainingQuestion.objects.create(session=new_session, ...)
        
        # Удаляем старую сессию
        session.delete()
```

## 3. Сериализатор (api/serializers.py)
- Добавлено поле `lesson_id` для записи при создании сессии
- В fields добавлено поле `lesson` для чтения

## Миграции
- Миграция `0001_initial.py` уже содержит поле `lesson` в модели TrainingSession
- Для применения на существующей БД可能需要 создать новую миграцию:
  ```bash
  python manage.py makemigrations api
  python manage.py migrate
  ```

## API Endpoints
Изменения обратно совместимы:
- `POST /api/training-sessions/from-result/<result_id>/` — теперь автоматически определяет lesson
- `GET /api/training-sessions/?user_id=<id>` — возвращает сессии с информацией о lesson
