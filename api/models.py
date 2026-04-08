# api/models.py
import uuid
from django.db import models
from django.contrib.auth.hashers import make_password

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=10, choices=[('student', 'Student'), ('teacher', 'Teacher')])

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.firstname} {self.lastname}"

class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'groups'

    def __str__(self):
        return self.name

class GroupMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')

    class Meta:
        db_table = 'group_members'
        unique_together = ('user', 'group')

    def __str__(self):
        return f"{self.user} in {self.group}"

class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'subjects'

    def __str__(self):
        return self.name

class Block(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='blocks')
    title = models.CharField(max_length=255)
    final_test = models.OneToOneField(
        'Test', on_delete=models.SET_NULL, null=True, blank=True, related_name='final_block_of'
    )
    lessons_count = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    position = models.IntegerField(default=0) # Для сортировки блоков в рамках предмета
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = 'blocks'
        ordering = ['position'] # Сортировка по умолчанию

    def __str__(self):
        return f"{self.title} ({self.subject.name})"

class Lesson(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='lessons')
    test = models.OneToOneField(
        'Test', on_delete=models.SET_NULL, null=True, blank=True, related_name='lesson_for'
    )
    video_link = models.URLField(blank=True, null=True)
    video_duration = models.IntegerField(null=True, blank=True) # в секундах
    summary = models.TextField(blank=True, null=True)
    duration = models.IntegerField(default=0) # продолжительность урока (например, видео + тест) в секундах
    position = models.IntegerField(default=0) # Для сортировки уроков в рамках блока
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = 'lessons'
        ordering = ['position'] # Сортировка по умолчанию

    def __str__(self):
        return f"Lesson {self.position}: {self.summary or self.block.title}"


class Test(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(default=0) # Длительность теста (таймер) в секундах
    is_published = models.BooleanField(default=False)


    class Meta:
        db_table = 'tests'

    def __str__(self):
        return self.title

class Question(models.Model):
    id = models.BigAutoField(primary_key=True)
    text = models.TextField()
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')

    class Meta:
        db_table = 'questions'

    def __str__(self):
        return self.text[:50] + "..."

class Answer(models.Model):
    id = models.BigAutoField(primary_key=True)
    text = models.TextField()
    is_correct = models.BooleanField()
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', null=True, blank=True)

    class Meta:
        db_table = 'answers'

    def __str__(self):
        return f"Answer for Q{id}: {'Correct' if self.is_correct else 'Incorrect'}"

class TestResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    score = models.IntegerField()
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='results', null=True, blank=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='results', null=True, blank=True)

    class Meta:
        db_table = 'test_results'

    def __str__(self):
        return f"{self.user} - {self.test} - Score: {self.score}"

class TestDifficulty(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Лёгкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ]
    id = models.BigAutoField(primary_key=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    avg_score_all = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    test = models.OneToOneField(Test, on_delete=models.CASCADE, related_name='difficulty')

    class Meta:
        db_table = 'test_difficulties'

    def __str__(self):
        return f"{self.test.title} - {self.difficulty}"

class StudentCluster(models.Model):
    id = models.BigAutoField(primary_key=True)
    cluster_id = models.IntegerField() # ID кластера (например, 0, 1, 2...)
    cluster_label = models.CharField(max_length=50) # Метка (например, "Слабый", "Средний", "Сильный")
    avg_score = models.FloatField(default=0)
    tests_taken = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cluster')

    class Meta:
        db_table = 'student_clusters'

    def __str__(self):
        return f"{self.user} - Cluster {self.cluster_id} ({self.cluster_label})"

class Recommendation(models.Model):
    id = models.BigAutoField(primary_key=True)
    text = models.TextField()
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    test = models.ForeignKey(Test, on_delete=models.SET_NULL, null=True, blank=True, related_name='recommendations')

    class Meta:
        db_table = 'recommendations'
        ordering = ['-priority', '-created_at'] # Сначала по приоритету, потом по времени

    def __str__(self):
        return f"Rec for {self.user} - Prio: {self.priority}"

class ScorePrediction(models.Model):
    id = models.BigAutoField(primary_key=True)
    predicted_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='predictions')

    class Meta:
        db_table = 'score_predictions'
        unique_together = ('user', 'test') # Один прогноз на юзера и тест

    def __str__(self):
        return f"Pred {self.user} - {self.test}: {self.predicted_score:.2f}"
