# api/models.py
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


# ═══════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstname  = models.CharField(max_length=100)
    lastname   = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100)
    email      = models.EmailField(unique=True)
    role       = models.CharField(
        max_length=10, 
        choices=[('student', 'Студент'), ('teacher', 'Преподаватель'), ('admin', 'Администратор')]
    )
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['firstname', 'lastname', 'patronymic', 'role']
    objects         = CustomUserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.firstname} {self.lastname} ({self.get_role_display()})"

    @property
    def password_hash(self):
        return self.password

    def has_teacher_permission(self):
        """Проверка прав преподавателя"""
        return self.role in ['teacher', 'admin']

    def has_admin_permission(self):
        """Проверка прав администратора"""
        return self.role == 'admin'


# ═══════════════════════════════════════════════════════════════════════
# GROUPS
# ═══════════════════════════════════════════════════════════════════════

class Group(models.Model):
    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'groups'

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    id    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user  = models.ForeignKey(User,  on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')

    class Meta:
        db_table       = 'group_members'
        unique_together = ('user', 'group')

    def __str__(self):
        return f"{self.user} in {self.group}"


# ═══════════════════════════════════════════════════════════════════════
# VIDEO  (NEW)
# ═══════════════════════════════════════════════════════════════════════

class VideoType(models.Model):
    id   = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'video_types'

    def __str__(self):
        return self.name


class Video(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Название видео"
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name="Описание"
    )

    video_file = models.FileField(
        upload_to='videos/',
        null=True,
        blank=True,
        verbose_name="Файл видео"
    )

    # Поле для ссылки (Rutube, YouTube и т.д.)
    link = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Ссылка на видео"
    )

    type = models.ForeignKey('VideoType', on_delete=models.CASCADE)
    duration = models.IntegerField(default=0)

    def get_video_url(self):
        if self.video_file:
            return self.video_file.url
        return self.link

    class Meta:
        db_table = 'videos'

    def __str__(self):
        return f"{self.name} ({self.type})"



# ═══════════════════════════════════════════════════════════════════════
# CONTENT STRUCTURE
# ═══════════════════════════════════════════════════════════════════════

class Subject(models.Model):
    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'subjects'
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'

    def __str__(self):
        return self.name


class Block(models.Model):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject        = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='blocks')
    title          = models.CharField(max_length=255)
    final_test     = models.OneToOneField(
        'Test', on_delete=models.SET_NULL, null=True, blank=True, related_name='final_block_of'
    )
    lessons_count  = models.IntegerField(default=0)
    description    = models.TextField(blank=True, null=True)
    position       = models.IntegerField(default=0)
    is_published   = models.BooleanField(default=False)

    class Meta:
        db_table = 'blocks'
        ordering = ['position']
        verbose_name = 'Блок'
        verbose_name_plural = 'Блоки'

    def __str__(self):
        return f"{self.title} ({self.subject.name})"


class Lesson(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block        = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='lessons')
    test         = models.OneToOneField(
        'Test', on_delete=models.SET_NULL, null=True, blank=True, related_name='lesson_for'
    )
    # ── видео ──
    video        = models.ForeignKey(
        Video, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons',
        help_text='Видеоматериал урока'
    )
    title        = models.CharField(max_length=255, blank=True, null=True)
    summary      = models.CharField(max_length=1000, blank=True, null=True)   # ← был TextField, теперь max 1000
    duration     = models.IntegerField(default=0, help_text='Суммарная длительность урока в секундах')
    position     = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = 'lessons'
        ordering = ['position']
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'

    def __str__(self):
        return self.title or self.summary or f"Lesson {self.position} in {self.block.title}"


# ═══════════════════════════════════════════════════════════════════════
# TESTS & QUESTIONS
# ═══════════════════════════════════════════════════════════════════════

class Test(models.Model):
    id           = models.BigAutoField(primary_key=True)
    title        = models.CharField(max_length=255)
    description  = models.TextField(blank=True, null=True)
    duration     = models.IntegerField(default=0, help_text='Таймер теста в секундах (0 = без ограничений)')
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = 'tests'
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return self.title


class Question(models.Model):
    id                       = models.BigAutoField(primary_key=True)
    text                     = models.TextField()
    test                     = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    recommendation_link      = models.URLField(
        max_length=2048, null=True, blank=True,
        help_text='Ссылка на текстовой материал для повторения по этому вопросу'
    )
    recommendation_video_link = models.URLField(
        max_length=2048, null=True, blank=True,
        help_text='Ссылка на видео для повторения по этому вопросу'
    )

    class Meta:
        db_table = 'questions'
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return self.text[:50] + "..."


class Answer(models.Model):
    id         = models.BigAutoField(primary_key=True)
    text       = models.TextField()
    is_correct = models.BooleanField()
    question   = models.ForeignKey(Question, on_delete=models.CASCADE,
                                   related_name='answers', null=True, blank=True)

    class Meta:
        db_table = 'answers'

    def __str__(self):
        return f"Answer for Q{self.question_id}: {'✓' if self.is_correct else '✗'}"


# ═══════════════════════════════════════════════════════════════════════
# TEST RESULTS
# ═══════════════════════════════════════════════════════════════════════

class TestResult(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    score        = models.IntegerField()
    started_at   = models.DateTimeField()
    completed_at = models.DateTimeField(auto_now_add=True)
    user         = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name='results', null=True, blank=True)
    test         = models.ForeignKey(Test, on_delete=models.CASCADE,
                                     related_name='results', null=True, blank=True)

    class Meta:
        db_table = 'test_results'

    def __str__(self):
        return f"{self.user} — {self.test} — {self.score}"


# ═══════════════════════════════════════════════════════════════════════
# TRAINER  (NEW)
# Сущности для тренажёра, который формируется из неправильных ответов
# ═══════════════════════════════════════════════════════════════════════

class UserAnswer(models.Model):

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test_result    = models.ForeignKey(TestResult, on_delete=models.CASCADE,
                                       related_name='user_answers')
    question       = models.ForeignKey(Question, on_delete=models.CASCADE,
                                       related_name='user_answers')
    chosen_answer  = models.ForeignKey(Answer, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='chosen_in')
    is_correct     = models.BooleanField(default=False)
    answered_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table       = 'user_answers'
        unique_together = ('test_result', 'question')   # один ответ на вопрос за попытку
        indexes         = [
            models.Index(fields=['test_result', 'is_correct']),  # быстрый поиск ошибок попытки
        ]

    def __str__(self):
        mark = '✓' if self.is_correct else '✗'
        return f"{self.test_result_id} | Q{self.question_id} [{mark}]"


class TrainingSession(models.Model):

    STATUS_CHOICES = [
        ('pending',    'Не начата'),
        ('active',     'В процессе'),
        ('completed',  'Завершена'),
    ]

    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user               = models.ForeignKey(User, on_delete=models.CASCADE,
                                           related_name='training_sessions')
    lesson             = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                                           null=True, blank=True, related_name='training_sessions',
                                           help_text='Урок, к которому относится сессия тренажёра')
    status             = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    source_test_result = models.ForeignKey(TestResult, on_delete=models.SET_NULL,
                                           null=True, blank=True,
                                           related_name='training_sessions',
                                           help_text='Попытка, по ошибкам которой создана сессия. '
                                                     'null = глобальный тренажёр')
    created_at         = models.DateTimeField(auto_now_add=True)
    completed_at       = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'training_sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'lesson', 'status']),  # быстрый поиск активных сессий по уроку
        ]

    def __str__(self):
        lesson_info = f" — Lesson {self.lesson.id}" if self.lesson else ""
        return f"Training {self.id} [{self.status}] — {self.user}{lesson_info}"


class TrainingQuestion(models.Model):

    STATUS_CHOICES = [
        ('pending',  'Ожидает ответа'),
        ('correct',  'Ответ верный'),
        ('wrong',    'Ответ неверный'),
        ('skipped',  'Пропущен'),
    ]

    id             = models.BigAutoField(primary_key=True)
    session        = models.ForeignKey(TrainingSession, on_delete=models.CASCADE,
                                       related_name='training_questions')
    question       = models.ForeignKey(Question, on_delete=models.CASCADE,
                                       related_name='training_questions')
    chosen_answer  = models.ForeignKey(Answer, on_delete=models.SET_NULL,
                                       null=True, blank=True,
                                       related_name='chosen_in_training')
    is_correct     = models.BooleanField(null=True, blank=True)   # null = ещё не отвечено
    position       = models.IntegerField(default=0)
    status         = models.CharField(max_length=8, choices=STATUS_CHOICES, default='pending')
    answered_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table       = 'training_questions'
        unique_together = ('session', 'question')
        ordering        = ['position']

    def __str__(self):
        return f"Session {self.session_id} | Q{self.question_id} [{self.status}]"


# ═══════════════════════════════════════════════════════════════════════
# ML
# ═══════════════════════════════════════════════════════════════════════

class TestDifficulty(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy',   'Лёгкий'),
        ('medium', 'Средний'),
        ('hard',   'Сложный'),
    ]
    id            = models.BigAutoField(primary_key=True)
    difficulty    = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    avg_score_all = models.FloatField(default=0)
    updated_at    = models.DateTimeField(auto_now=True)
    test          = models.OneToOneField(Test, on_delete=models.CASCADE, related_name='difficulty')

    class Meta:
        db_table = 'test_difficulties'

    def __str__(self):
        return f"{self.test.title} — {self.difficulty}"


class StudentCluster(models.Model):
    id            = models.BigAutoField(primary_key=True)
    cluster_id    = models.IntegerField()
    cluster_label = models.CharField(max_length=50)
    avg_score     = models.FloatField(default=0)
    tests_taken   = models.IntegerField(default=0)
    updated_at    = models.DateTimeField(auto_now=True)
    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cluster')

    class Meta:
        db_table = 'student_clusters'
        verbose_name = 'Кластер студента'
        verbose_name_plural = 'Кластеры студентов'

    def __str__(self):
        return f"{self.user} — Cluster {self.cluster_id} ({self.cluster_label})"


class Recommendation(models.Model):
    id         = models.BigAutoField(primary_key=True)
    text       = models.TextField()
    priority   = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    test       = models.ForeignKey(Test, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='recommendations')

    class Meta:
        db_table = 'recommendations'
        ordering = ['-priority', '-created_at']
        verbose_name = 'Рекомендация'
        verbose_name_plural = 'Рекомендации'

    def __str__(self):
        return f"Rec for {self.user} — Prio: {self.priority}"


class ScorePrediction(models.Model):
    id              = models.BigAutoField(primary_key=True)
    predicted_score = models.FloatField()
    created_at      = models.DateTimeField(auto_now_add=True)
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    test            = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='predictions')

    class Meta:
        db_table       = 'score_predictions'
        unique_together = ('user', 'test')

    def __str__(self):
        return f"Pred {self.user} — {self.test}: {self.predicted_score:.2f}"