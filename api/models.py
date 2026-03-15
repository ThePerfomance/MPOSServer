import uuid
from django.db import models


# ─────────────────────────────────────────────
# Базовые таблицы (порт с Rust-сервера)
# ─────────────────────────────────────────────

class User(models.Model):
    ROLE_CHOICES = [("student", "Student"), ("teacher", "Teacher")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    class Meta:
        db_table = "users"


class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "groups"


class GroupMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="group_memberships")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")

    class Meta:
        db_table = "group_members"
        unique_together = ("user", "group")


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "subjects"


class Test(models.Model):
    # id — автоинкремент, как в Rust-версии (SERIAL)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    subject = models.ForeignKey(
        Subject, on_delete=models.SET_NULL, null=True, blank=True, related_name="tests"
    )

    class Meta:
        db_table = "tests"


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=True, blank=True, related_name="questions")
    text = models.TextField()

    class Meta:
        db_table = "questions"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True, related_name="answers")
    text = models.TextField()
    is_correct = models.BooleanField()

    class Meta:
        db_table = "answers"


class TestResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="results")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, null=True, blank=True, related_name="results")
    score = models.IntegerField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)  # выставляется сервером при создании

    class Meta:
        db_table = "test_results"


# ─────────────────────────────────────────────
# ML-расширения базы данных
# ─────────────────────────────────────────────

class StudentCluster(models.Model):
    """
    Результат кластеризации студента (KMeans).
    Обновляется при вызове /ml/cluster-students.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cluster")
    cluster_id = models.IntegerField()          # номер кластера (0, 1, 2, ...)
    cluster_label = models.CharField(max_length=50)  # "слабый", "средний", "сильный"
    avg_score = models.FloatField(default=0)
    tests_taken = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_clusters"


class TestDifficulty(models.Model):
    """
    Сегментация теста по уровню сложности.
    Обновляется при вызове /ml/segment-tests.
    """
    DIFFICULTY_CHOICES = [
        ("easy", "Лёгкий"),
        ("medium", "Средний"),
        ("hard", "Сложный"),
    ]
    test = models.OneToOneField(Test, on_delete=models.CASCADE, related_name="difficulty")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    avg_score_all = models.FloatField(default=0)   # средний балл по всем студентам
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "test_difficulties"


class ScorePrediction(models.Model):
    """
    Прогноз результата студента для конкретного теста (линейная регрессия).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="predictions")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="predictions")
    predicted_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "score_predictions"
        unique_together = ("user", "test")


class Recommendation(models.Model):
    """
    Рекомендации по обучению для конкретного студента.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recommendations")
    test = models.ForeignKey(
        Test, on_delete=models.SET_NULL, null=True, blank=True, related_name="recommendations"
    )
    text = models.TextField()   # текст рекомендации
    priority = models.IntegerField(default=0)  # чем выше — тем важнее
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendations"
        ordering = ["-priority", "-created_at"]