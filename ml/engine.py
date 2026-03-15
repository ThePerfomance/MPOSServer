"""
ml/engine.py — вся ML-логика приложения.

Алгоритм кластеризации полностью перенесён с Android:
  • 5 признаков: accuracy, attempts, time_spent, test_count, weighted_difficulty
  • Нормализация Min-Max
  • PCA до 2D
  • KMeans (K=5) с 10 запусками, выбор по Silhouette
  • Ранги: S, A, B, C, D (по убыванию среднего первого PCA-компонента)
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import silhouette_score
from sklearn.linear_model import LinearRegression


# ─────────────────────────────────────────────────────────────────────
# Константы — совпадают с Android KMeans.kt
# ─────────────────────────────────────────────────────────────────────
K = 5
RANK_LABELS = ["S", "A", "B", "C", "D"]
WEIGHTS = [0.6, 0.1, 0.2, 0.05, 0.05]  # accuracy, attempts, time, testCount, difficulty


# ─────────────────────────────────────────────────────────────────────
# 1. Кластеризация студентов (перенос с Android KMeans.kt)
# ─────────────────────────────────────────────────────────────────────

def cluster_students(student_stats: list[dict], n_clusters: int = 5) -> dict:
    """
    Параметры
    ---------
    student_stats : список словарей
        [{
            "user_id": str,
            "avg_score": float,       # средний балл (accuracy)
            "tests_taken": int,       # количество попыток
            "avg_time": float,        # среднее время выполнения (минуты)
            "test_count": int,        # количество уникальных тестов
            "weighted_difficulty": float  # средневзвешенная сложность
        }, ...]

    Возвращает
    ----------
    {
        "clusters": [{"user_id", "rank", "cluster_id", "avg_score", "pca_x", "pca_y"}, ...],
        "pca_points": [{"user_id", "x", "y", "cluster_id", "rank"}, ...],
        "metrics": {"silhouette": float, "inertia": float}
    }
    """
    if not student_stats:
        return {"clusters": [], "pca_points": [], "metrics": {}}

    n = len(student_stats)

    # Если студентов меньше 2 — кластеризация невозможна, всем даём ранг A
    if n < 2:
        s = student_stats[0]
        return {
            "clusters": [{
                "user_id": s["user_id"], "cluster_id": 0, "rank": "A",
                "avg_score": s.get("avg_score", 0), "tests_taken": s.get("tests_taken", 0),
                "pca_x": 0.0, "pca_y": 0.0,
            }],
            "pca_points": [{"user_id": s["user_id"], "x": 0.0, "y": 0.0,
                            "cluster_id": 0, "rank": "A",
                            "firstname": s.get("firstname",""), "lastname": s.get("lastname","")}],
            "metrics": {"silhouette": 0.0, "inertia": 0.0},
        }

    # K не может быть больше числа студентов
    n_clusters = min(n_clusters, n)

    # 1. Формируем матрицу признаков (как в Android)
    X_raw = np.array([
        [
            s.get("avg_score", 0),
            s.get("tests_taken", 0),
            s.get("avg_time", 0),
            s.get("test_count", 0),
            s.get("weighted_difficulty", 0),
        ]
        for s in student_stats
    ], dtype=float)

    # 2. Нормализация Min-Max
    scaler = MinMaxScaler()
    X_norm = scaler.fit_transform(X_raw)

    # 3. Применяем веса
    X_weighted = X_norm * np.array(WEIGHTS)

    # 4. PCA до 2D
    # n_components <= min(n_samples - 1, n_features) — ограничение sklearn
    n_components = min(2, X_weighted.shape[0] - 1, X_weighted.shape[1])
    n_components = max(1, n_components)  # минимум 1
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_weighted)

    # Всегда 2 колонки для графика
    if X_pca.shape[1] == 1:
        X_pca = np.hstack([X_pca, np.zeros((X_pca.shape[0], 1))])

    # 5. KMeans — 10 запусков, выбираем лучший по Silhouette (как в Android)
    best_labels = None
    best_score = -1.0
    best_inertia = 0.0

    for _ in range(10):
        km = KMeans(n_clusters=n_clusters, random_state=None, n_init=1)
        labels = km.fit_predict(X_pca)

        if len(set(labels)) < 2:
            # Если все в одном кластере — silhouette недоступен
            if best_labels is None:
                best_labels = labels.copy()
                best_inertia = float(km.inertia_)
            continue
        try:
            score = silhouette_score(X_pca, labels)
        except Exception:
            score = -1.0

        if score > best_score:
            best_score = score
            best_labels = labels.copy()
            best_inertia = float(km.inertia_)

    if best_labels is None:
        best_labels = np.zeros(n, dtype=int)

    # Для 2 студентов silhouette не считается — ставим 0
    if best_score < 0 and len(set(best_labels)) < 2:
        best_score = 0.0

    # 6. Сортируем кластеры по убыванию среднего PCA[0] → назначаем ранги S..D
    cluster_pca0_means = {}
    for i, cid in enumerate(best_labels):
        cluster_pca0_means.setdefault(int(cid), []).append(float(X_pca[i, 0]))
    sorted_clusters = sorted(cluster_pca0_means.keys(),
                              key=lambda c: np.mean(cluster_pca0_means[c]),
                              reverse=True)
    cluster_to_rank = {cid: RANK_LABELS[i] if i < len(RANK_LABELS) else "X"
                       for i, cid in enumerate(sorted_clusters)}

    # 7. Собираем результат
    clusters_out = []
    pca_points = []
    for i, s in enumerate(student_stats):
        cid = int(best_labels[i])
        rank = cluster_to_rank.get(cid, "X")
        clusters_out.append({
            "user_id":    s["user_id"],
            "cluster_id": cid,
            "rank":       rank,
            "avg_score":  s.get("avg_score", 0),
            "tests_taken": s.get("tests_taken", 0),
            "pca_x":      float(X_pca[i, 0]),
            "pca_y":      float(X_pca[i, 1]),
        })
        pca_points.append({
            "user_id":    s["user_id"],
            "x":          float(X_pca[i, 0]),
            "y":          float(X_pca[i, 1]),
            "cluster_id": cid,
            "rank":       rank,
        })

    return {
        "clusters":   clusters_out,
        "pca_points": pca_points,
        "metrics": {
            "silhouette": round(best_score, 4),
            "inertia":    round(best_inertia, 4),
        },
    }


# ─────────────────────────────────────────────────────────────────────
# 2. Сегментация тестов по сложности
# ─────────────────────────────────────────────────────────────────────

def _difficulty_label(avg: float, low_thr: float, high_thr: float) -> str:
    if avg >= high_thr:
        return "easy"
    if avg >= low_thr:
        return "medium"
    return "hard"


def segment_tests(test_stats: list[dict]) -> list[dict]:
    if not test_stats:
        return []
    scores = [t["avg_score"] for t in test_stats]
    low_thr  = float(np.percentile(scores, 33))
    high_thr = float(np.percentile(scores, 66))
    return [
        {
            "test_id":    t["test_id"],
            "difficulty": _difficulty_label(t["avg_score"], low_thr, high_thr),
            "avg_score":  t["avg_score"],
        }
        for t in test_stats
    ]


# ─────────────────────────────────────────────────────────────────────
# 3. Прогнозирование результата
# ─────────────────────────────────────────────────────────────────────

def predict_score(history: list[dict], test_avg_score: float) -> float:
    if len(history) < 2:
        return float(np.mean([h["score"] for h in history])) if history else test_avg_score
    X = np.array([[h["test_avg"]] for h in history], dtype=float)
    y = np.array([h["score"]     for h in history], dtype=float)
    model = LinearRegression()
    model.fit(X, y)
    return float(np.clip(model.predict([[test_avg_score]])[0], 0, 100))


# ─────────────────────────────────────────────────────────────────────
# 4. Рекомендации
# ─────────────────────────────────────────────────────────────────────

# Маппинг (rank, difficulty) → (текст, приоритет)
_REC_MAP = {
    ("S", "hard"):   ("Отличный результат! Сложный тест полностью соответствует вашему уровню.", 6),
    ("S", "medium"): ("Рекомендуем попробовать тесты повышенной сложности.", 3),
    ("S", "easy"):   ("Этот тест для вас прост — попробуйте более сложный материал.", 2),
    ("A", "hard"):   ("Тест повышенной сложности: рекомендуем повторить тему перед прохождением.", 9),
    ("A", "medium"): ("Тест соответствует вашему уровню. Удачи!", 4),
    ("A", "easy"):   ("Лёгкий тест отлично подойдёт для закрепления материала.", 3),
    ("B", "hard"):   ("Сложный тест: рекомендуем сначала пройти средние.", 8),
    ("B", "medium"): ("Хороший выбор — тест среднего уровня для вашего уровня.", 5),
    ("B", "easy"):   ("Лёгкий тест поможет повторить основы.", 4),
    ("C", "hard"):   ("Рекомендуем начать с лёгких тестов по данной теме, чтобы укрепить базу.", 10),
    ("C", "medium"): ("Пройдите дополнительные материалы перед выполнением теста среднего уровня.", 8),
    ("C", "easy"):   ("Пройдите лёгкий тест — он поможет вам набрать уверенность.", 5),
    ("D", "hard"):   ("Этот тест пока слишком сложный. Начните с лёгких тестов.", 10),
    ("D", "medium"): ("Рекомендуем сначала изучить базовые материалы.", 9),
    ("D", "easy"):   ("Начните с лёгкого теста — это поможет освоить основы.", 7),
}
_DEFAULT_REC = ("Продолжайте регулярно проходить тесты для улучшения результатов.", 1)


def build_recommendations(rank: str, tests_with_difficulty: list[dict]) -> list[dict]:
    results = []
    for t in tests_with_difficulty:
        text, priority = _REC_MAP.get((rank, t["difficulty"]), _DEFAULT_REC)
        results.append({"test_id": t["test_id"], "text": text, "priority": priority})
    results.sort(key=lambda r: -r["priority"])
    return results