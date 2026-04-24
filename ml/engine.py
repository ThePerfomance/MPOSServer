"""
ml/engine.py — вся ML-логика приложения для диплома.

Концепция: Анализ результатов тестирования на уровне каждого вопроса → 
персонализированные рекомендации по темам с ссылками на материалы.

Алгоритмы:
  • Анализ ошибок по каждому вопросу
  • Определение слабых тем (topics)
  • Генерация рекомендаций с ссылками на источники
  • Персонализация на основе истории ответов пользователя
"""

import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════════════════════════════
# 1. АНАЛИЗ ОШИБОК ПО ТЕМAM
# ═══════════════════════════════════════════════════════════════════════

def analyze_weak_topics(user_answers: list[dict], questions_map: dict) -> dict:
    """
    Анализирует ответы пользователя и определяет слабые темы.
    
    Параметры
    ---------
    user_answers : список словарей
        [{
            "question_id": int,
            "is_correct": bool,
            "answered_at": str (ISO datetime),
            "test_id": int,
        }, ...]
    
    questions_map : словарь
        {question_id: {"topic": str, "block_id": str, "lesson_id": str, 
                       "recommendation_link": str, "recommendation_video_link": str}, ...}
    
    Возвращает
    ----------
    {
        "weak_topics": [{"topic": str, "error_rate": float, "error_count": int, 
                         "total_attempts": int, "last_error_at": str}, ...],
        "topic_details": {topic: {"questions": [...], "resources": [...]}},
        "overall_stats": {"total_questions": int, "correct": int, "accuracy": float}
    }
    """
    if not user_answers:
        return {
            "weak_topics": [],
            "topic_details": {},
            "overall_stats": {"total_questions": 0, "correct": 0, "accuracy": 0.0}
        }
    
    # Статистика по темам
    topic_stats = defaultdict(lambda: {
        "correct": 0,
        "incorrect": 0,
        "questions": [],
        "resources": set(),
        "last_error_at": None
    })
    
    total_correct = 0
    total_questions = 0
    
    for ans in user_answers:
        q_id = ans["question_id"]
        is_correct = ans["is_correct"]
        answered_at = ans.get("answered_at")
        
        if q_id not in questions_map:
            continue
        
        q_info = questions_map[q_id]
        topic = q_info.get("topic", "Общая тема")
        
        total_questions += 1
        if is_correct:
            total_correct += 1
            topic_stats[topic]["correct"] += 1
        else:
            topic_stats[topic]["incorrect"] += 1
            topic_stats[topic]["questions"].append(q_id)
            
            # Обновляем время последней ошибки
            if answered_at:
                if topic_stats[topic]["last_error_at"] is None:
                    topic_stats[topic]["last_error_at"] = answered_at
                else:
                    if answered_at > topic_stats[topic]["last_error_at"]:
                        topic_stats[topic]["last_error_at"] = answered_at
            
            # Добавляем ресурсы для повторения
            if q_info.get("recommendation_link"):
                topic_stats[topic]["resources"].add(q_info["recommendation_link"])
            if q_info.get("recommendation_video_link"):
                topic_stats[topic]["resources"].add(q_info["recommendation_video_link"])
    
    # Вычисляем error_rate и формируем список слабых тем
    weak_topics = []
    for topic, stats in topic_stats.items():
        total_attempts = stats["correct"] + stats["incorrect"]
        if total_attempts == 0:
            continue
        
        error_rate = stats["incorrect"] / total_attempts
        
        # Тема считается слабой, если error_rate > 0.3 (30% ошибок)
        if error_rate > 0.3:
            weak_topics.append({
                "topic": topic,
                "error_rate": round(error_rate, 3),
                "error_count": stats["incorrect"],
                "total_attempts": total_attempts,
                "last_error_at": stats["last_error_at"],
            })
    
    # Сортируем по error_rate (самые проблемные первыми)
    weak_topics.sort(key=lambda x: (-x["error_rate"], -x["error_count"]))
    
    # Формируем детали по темам
    topic_details = {}
    for topic, stats in topic_stats.items():
        topic_details[topic] = {
            "questions": list(set(stats["questions"])),
            "resources": list(stats["resources"]),
            "accuracy": round(stats["correct"] / (stats["correct"] + stats["incorrect"]), 3)
            if (stats["correct"] + stats["incorrect"]) > 0 else 0.0
        }
    
    return {
        "weak_topics": weak_topics,
        "topic_details": topic_details,
        "overall_stats": {
            "total_questions": total_questions,
            "correct": total_correct,
            "accuracy": round(total_correct / total_questions, 3) if total_questions > 0 else 0.0
        }
    }


# ═══════════════════════════════════════════════════════════════════════
# 2. ГЕНЕРАЦИЯ ПЕРСОНАЛИЗИРОВАННЫХ РЕКОМЕНДАЦИЙ
# ═══════════════════════════════════════════════════════════════════════

def generate_personalized_recommendations(
    weak_topics_analysis: dict,
    lessons_map: dict,
    videos_map: dict,
    blocks_map: dict,
    min_priority: int = 1,
    max_recommendations: int = 10
) -> list[dict]:
    """
    Генерирует персонализированные рекомендации на основе слабых тем.
    
    Параметры
    ---------
    weak_topics_analysis : dict
        Результат функции analyze_weak_topics()
    
    lessons_map : dict
        {lesson_id: {"title": str, "summary": str, "block_id": str, "video_id": str}, ...}
    
    videos_map : dict
        {video_id: {"title": str, "link": str, "type": str}, ...}
    
    blocks_map : dict
        {block_id: {"title": str, "subject_id": str}, ...}
    
    Возвращает
    ----------
    [
        {
            "topic": str,
            "priority": int,  # 1-10, где 10 - самый высокий приоритет
            "recommendation_text": str,
            "resources": [
                {"type": "lesson", "title": str, "url": str},
                {"type": "video", "title": str, "url": str},
                {"type": "link", "title": str, "url": str}
            ],
            "practice_questions": [question_id, ...]
        },
        ...
    ]
    """
    recommendations = []
    
    weak_topics = weak_topics_analysis.get("weak_topics", [])
    topic_details = weak_topics_analysis.get("topic_details", {})
    
    for idx, weak_topic in enumerate(weak_topics[:max_recommendations]):
        topic = weak_topic["topic"]
        error_rate = weak_topic["error_rate"]
        error_count = weak_topic["error_count"]
        
        # Приоритет: чем выше error_rate и больше ошибок, тем выше приоритет
        priority = min(10, max(1, int(error_rate * 10) + (error_count // 3)))
        
        if priority < min_priority:
            continue
        
        # Формируем текст рекомендации
        if error_rate >= 0.7:
            rec_text = f"Критическая проблема по теме '{topic}'. Необходимо срочно повторить материал."
        elif error_rate >= 0.5:
            rec_text = f"Рекомендуется повторить тему '{topic}' — высокий процент ошибок."
        elif error_rate >= 0.3:
            rec_text = f"Стоит обратить внимание на тему '{topic}' для улучшения результатов."
        else:
            rec_text = f"Тема '{topic}' требует небольшого повторения."
        
        # Собираем ресурсы для повторения
        resources = []
        practice_questions = topic_details.get(topic, {}).get("questions", [])
        
        # Ищем уроки по этой теме (через block → subject matching)
        for lesson_id, lesson_info in lessons_map.items():
            lesson_title = lesson_info.get("title", "")
            lesson_summary = lesson_info.get("summary", "")
            
            # Проверяем, относится ли урок к этой теме (по названию или описанию)
            if _topic_matches(lesson_title, lesson_summary, topic):
                # Добавляем конспект урока
                if lesson_summary:
                    resources.append({
                        "type": "lesson",
                        "title": f"Конспект: {lesson_title}",
                        "url": f"/lessons/{lesson_id}/",
                        "content": lesson_summary[:500]  # Краткое содержание
                    })
                
                # Добавляем видео, если есть
                video_id = lesson_info.get("video_id")
                if video_id and video_id in videos_map:
                    video_info = videos_map[video_id]
                    video_url = video_info.get("link", "")
                    if video_url:
                        resources.append({
                            "type": "video",
                            "title": f"Видео: {video_info.get('title', 'Обучающее видео')}",
                            "url": video_url
                        })
        
        # Добавляем внешние ссылки из вопросов
        topic_resources = topic_details.get(topic, {}).get("resources", [])
        for res_url in topic_resources[:3]:  # Максимум 3 внешних ссылки
            resources.append({
                "type": "link",
                "title": "Материал для повторения",
                "url": res_url
            })
        
        # Если ресурсов нет, добавляем общую рекомендацию
        if not resources:
            resources.append({
                "type": "general",
                "title": f"Повторите тему '{topic}'",
                "url": "",
                "description": "Рекомендуется изучить материалы по данной теме в учебнике или обратиться к преподавателю."
            })
        
        recommendations.append({
            "topic": topic,
            "priority": priority,
            "recommendation_text": rec_text,
            "resources": resources,
            "practice_questions": practice_questions[:5],  # Максимум 5 вопросов для практики
            "error_rate": error_rate,
            "error_count": error_count
        })
    
    # Сортируем по приоритету
    recommendations.sort(key=lambda x: -x["priority"])
    
    return recommendations


def _topic_matches(title: str, summary: str, topic: str) -> bool:
    """Проверяет, относится ли урок/материал к заданной теме."""
    if not title and not summary:
        return False
    
    text = f"{title} {summary}".lower()
    topic_lower = topic.lower()
    
    # Простая проверка на вхождение
    if topic_lower in text:
        return True
    
    # Проверка на частичное совпадение (если тема состоит из нескольких слов)
    topic_words = topic_lower.split()
    if len(topic_words) > 1:
        matches = sum(1 for word in topic_words if word in text)
        if matches >= len(topic_words) // 2 + 1:
            return True
    
    return False


# ═══════════════════════════════════════════════════════════════════════
# 3. АНАЛИЗ ПРОГРЕССА ПО ВРЕМЕНИ
# ═══════════════════════════════════════════════════════════════════════

def analyze_progress_over_time(user_answers: list[dict], window_days: int = 7) -> dict:
    """
    Анализирует прогресс пользователя по времени.
    
    Параметры
    ---------
    user_answers : список словарей
        [{
            "question_id": int,
            "is_correct": bool,
            "answered_at": str (ISO datetime),
        }, ...]
    
    window_days : int
        Размер окна анализа в днях
    
    Возвращает
    ----------
    {
        "trend": "improving" | "declining" | "stable",
        "periods": [
            {"period": "2024-01-01 to 2024-01-07", "accuracy": 0.75, "questions": 20},
            ...
        ],
        "recommendation": str
    }
    """
    if not user_answers:
        return {
            "trend": "stable",
            "periods": [],
            "recommendation": "Недостаточно данных для анализа прогресса"
        }
    
    # Группируем ответы по периодам
    now = datetime.now()
    periods = defaultdict(lambda: {"correct": 0, "total": 0})
    
    for ans in user_answers:
        answered_at = ans.get("answered_at")
        if not answered_at:
            continue
        
        try:
            dt = datetime.fromisoformat(answered_at.replace('Z', '+00:00'))
        except:
            continue
        
        # Определяем номер периода
        days_ago = (now - dt).days
        if days_ago < 0:
            continue
        
        period_num = days_ago // window_days
        period_start = now - timedelta(days=(period_num + 1) * window_days)
        period_end = now - timedelta(days=period_num * window_days)
        
        period_key = f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
        
        periods[period_key]["total"] += 1
        if ans["is_correct"]:
            periods[period_key]["correct"] += 1
    
    if len(periods) < 2:
        return {
            "trend": "stable",
            "periods": [],
            "recommendation": "Недостаточно данных для анализа тренда"
        }
    
    # Вычисляем точность по периодам
    period_stats = []
    for period_key in sorted(periods.keys()):
        stats = periods[period_key]
        accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        period_stats.append({
            "period": period_key,
            "accuracy": round(accuracy, 3),
            "questions": stats["total"]
        })
    
    # Определяем тренд
    if len(period_stats) >= 2:
        recent_accuracy = period_stats[-1]["accuracy"]
        previous_accuracy = period_stats[-2]["accuracy"]
        
        diff = recent_accuracy - previous_accuracy
        
        if diff > 0.1:
            trend = "improving"
            recommendation = "Отличный прогресс! Продолжайте в том же духе."
        elif diff < -0.1:
            trend = "declining"
            recommendation = "Результаты ухудшились. Рекомендуется повторить пройденный материал."
        else:
            trend = "stable"
            recommendation = "Стабильный результат. Попробуйте увеличить сложность заданий."
    else:
        trend = "stable"
        recommendation = "Продолжайте обучение для сбора статистики."
    
    return {
        "trend": trend,
        "periods": period_stats,
        "recommendation": recommendation
    }


# ═══════════════════════════════════════════════════════════════════════
# 4. ПОДБОР ИНДИВИДУАЛЬНОЙ ТРАЕКТОРИИ ОБУЧЕНИЯ
# ═══════════════════════════════════════════════════════════════════════

def build_learning_path(
    weak_topics_analysis: dict,
    recommendations: list[dict],
    blocks_structure: dict
) -> list[dict]:
    """
    Строит индивидуальную траекторию обучения на основе слабых тем.
    
    Параметры
    ---------
    weak_topics_analysis : dict
        Результат analyze_weak_topics()
    
    recommendations : list[dict]
        Результат generate_personalized_recommendations()
    
    blocks_structure : dict
        {
            "blocks": [
                {"id": str, "title": str, "subject": str, "position": int},
                ...
            ],
            "lessons_by_block": {
                block_id: [{"id": str, "title": str, "position": int}, ...]
            }
        }
    
    Возвращает
    ----------
    [
        {
            "step": int,
            "action": "study" | "practice" | "test",
            "topic": str,
            "resource": dict,
            "estimated_time_minutes": int
        },
        ...
    ]
    """
    learning_path = []
    step = 1
    
    for rec in recommendations[:5]:  # Максимум 5 шагов
        topic = rec["topic"]
        
        # Шаг 1: Изучение теории
        for resource in rec["resources"]:
            if resource["type"] == "lesson":
                learning_path.append({
                    "step": step,
                    "action": "study",
                    "topic": topic,
                    "resource": resource,
                    "estimated_time_minutes": 15
                })
                step += 1
        
        # Шаг 2: Просмотр видео
        for resource in rec["resources"]:
            if resource["type"] == "video":
                learning_path.append({
                    "step": step,
                    "action": "watch",
                    "topic": topic,
                    "resource": resource,
                    "estimated_time_minutes": 10
                })
                step += 1
        
        # Шаг 3: Практика
        if rec["practice_questions"]:
            learning_path.append({
                "step": step,
                "action": "practice",
                "topic": topic,
                "question_ids": rec["practice_questions"],
                "estimated_time_minutes": 20
            })
            step += 1
    
    return learning_path