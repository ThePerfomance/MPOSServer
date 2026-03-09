"""
ml/engine.py  —  вся ML-логика приложения.

Используемые алгоритмы:
  • KMeans             — кластеризация студентов по успеваемости
  • KMeans (3 класса) — сегментация тестов по сложности
  • LinearRegression   — прогнозирование результатов
  Рекомендации строятся на основе кластера студента и сложности теста.
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


# ─────────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ─────────────────────────────────────────────────────────────────────

def _label_for_cluster(mean_scores: list[float], cluster_id: int) -> str:
    """
    Присваивает кластерам читаемые метки по средним баллам.
    Сортируем центры и маппим: низкий → 'слабый', средний → 'средний', высокий → 'сильный'.
    """
    sorted_ids = sorted(range(len(mean_scores)), key=lambda i: mean_scores[i])
    labels = ["слабый", "средний", "сильный"]
    rank = sorted_ids.index(cluster_id)
    # Если кластеров < 3 — берём усечённый список меток
    available = labels[len(labels) - len(sorted_ids):]
    return available[rank]


def _difficulty_label(avg: float, low_thr: float, high_thr: float) -> str:
    if avg >= high_thr:
        return "easy"
    if avg >= low_thr:
        return "medium"
    return "hard"


# ─────────────────────────────────────────────────────────────────────
# 1. Кластеризация студентов
# ─────────────────────────────────────────────────────────────────────

def cluster_students(student_stats: list[dict], n_clusters: int = 3) -> list[dict]:
    """
    Параметры
    ---------
    student_stats : список словарей
        [{"user_id": uuid_str, "avg_score": float, "tests_taken": int}, ...]
    n_clusters : количество кластеров (по умолчанию 3)

    Возвращает
    ----------
    список словарей
        [{"user_id": ..., "cluster_id": int, "cluster_label": str}, ...]
    """
    if not student_stats:
        return []

    n_clusters = min(n_clusters, len(student_stats))

    X = np.array([[s["avg_score"], s["tests_taken"]] for s in student_stats], dtype=float)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    # Средний балл по каждому кластеру (для читаемых меток)
    cluster_avgs = []
    for c in range(n_clusters):
        mask = labels == c
        cluster_avgs.append(float(X[mask, 0].mean()) if mask.any() else 0.0)

    results = []
    for i, s in enumerate(student_stats):
        cid = int(labels[i])
        results.append({
            "user_id": s["user_id"],
            "cluster_id": cid,
            "cluster_label": _label_for_cluster(cluster_avgs, cid),
            "avg_score": s["avg_score"],
            "tests_taken": s["tests_taken"],
        })
    return results


# ─────────────────────────────────────────────────────────────────────
# 2. Сегментация тестов по сложности
# ─────────────────────────────────────────────────────────────────────

def segment_tests(test_stats: list[dict]) -> list[dict]:
    """
    Параметры
    ---------
    test_stats : [{"test_id": int, "avg_score": float, "attempt_count": int}, ...]

    Возвращает
    ----------
    [{"test_id": int, "difficulty": str, "avg_score": float}, ...]
    """
    if not test_stats:
        return []

    scores = [t["avg_score"] for t in test_stats]
    low_thr = float(np.percentile(scores, 33))
    high_thr = float(np.percentile(scores, 66))

    results = []
    for t in test_stats:
        results.append({
            "test_id": t["test_id"],
            "difficulty": _difficulty_label(t["avg_score"], low_thr, high_thr),
            "avg_score": t["avg_score"],
        })
    return results


# ─────────────────────────────────────────────────────────────────────
# 3. Прогнозирование результата
# ─────────────────────────────────────────────────────────────────────

def predict_score(history: list[dict], test_avg_score: float) -> float:
    """
    Прогнозирует балл студента для нового теста.

    Параметры
    ---------
    history : прошлые результаты студента
        [{"score": int, "test_avg": float}, ...]
        (test_avg — средний балл по этому тесту среди всех студентов)
    test_avg_score : средний балл целевого теста

    Возвращает
    ----------
    predicted_score : float  (обрезан до [0, 100])
    """
    if len(history) < 2:
        # Недостаточно данных — возвращаем личный средний или avg теста
        if history:
            return float(np.mean([h["score"] for h in history]))
        return test_avg_score

    X = np.array([[h["test_avg"]] for h in history], dtype=float)
    y = np.array([h["score"] for h in history], dtype=float)

    model = LinearRegression()
    model.fit(X, y)
    predicted = model.predict([[test_avg_score]])[0]
    return float(np.clip(predicted, 0, 100))


# ─────────────────────────────────────────────────────────────────────
# 4. Генерация рекомендаций
# ─────────────────────────────────────────────────────────────────────

_RECOMMENDATION_MAP = {
    # (cluster_label, difficulty) → (текст рекомендации, приоритет)
    ("слабый", "hard"):   ("Рекомендуем начать с лёгких тестов по данной теме, чтобы укрепить базу.", 10),
    ("слабый", "medium"): ("Пройдите дополнительные материалы перед выполнением теста среднего уровня.", 8),
    ("слабый", "easy"):   ("Пройдите лёгкий тест — он поможет вам набрать уверенность.", 5),
    ("средний", "hard"):  ("Тест повышенной сложности: рекомендуем повторить тему перед прохождением.", 9),
    ("средний", "medium"):("Тест соответствует вашему уровню. Удачи!", 4),
    ("средний", "easy"):  ("Лёгкий тест отлично подойдёт для закрепления материала.", 3),
    ("сильный", "hard"):  ("Сложный тест соответствует вашему высокому уровню.", 6),
    ("сильный", "medium"):("Рекомендуем попробовать тесты повышенной сложности.", 3),
    ("сильный", "easy"):  ("Этот тест для вас прост — попробуйте более сложный материал.", 2),
}

_DEFAULT_REC = ("Продолжайте регулярно проходить тесты для улучшения результатов.", 1)


def build_recommendations(
    cluster_label: str,
    tests_with_difficulty: list[dict],
) -> list[dict]:
    """
    Параметры
    ---------
    cluster_label : метка кластера студента ("слабый" / "средний" / "сильный")
    tests_with_difficulty : [{"test_id": int, "difficulty": str}, ...]

    Возвращает
    ----------
    [{"test_id": int, "text": str, "priority": int}, ...]
    """
    results = []
    for t in tests_with_difficulty:
        text, priority = _RECOMMENDATION_MAP.get(
            (cluster_label, t["difficulty"]), _DEFAULT_REC
        )
        results.append({
            "test_id": t["test_id"],
            "text": text,
            "priority": priority,
        })
    # Сортируем по убыванию приоритета
    results.sort(key=lambda r: -r["priority"])
    return results
