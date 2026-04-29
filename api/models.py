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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstname = models.CharField("Имя", max_length=100)
    lastname = models.CharField("Фамилия", max_length=100)
    patronymic = models.CharField("Отчество", max_length=100)
    email = models.EmailField("Email адрес", unique=True)
    role       = models.CharField(
        "Роль",
        max_length=10,
        choices=[('student', 'Студент'), ('teacher', 'Преподаватель'), ('admin', 'Администратор')]
    )
    is_active = models.BooleanField("Активен", default=True, help_text="Активация аккаунта пользователя")
    is_staff = models.BooleanField("Статус персонала", default=False, help_text="Является ли пользователь персоналом")

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
    id   = models.UUIDField("ИД Группы",primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Название группы",max_length=100, unique=True)

    class Meta:
        db_table = 'groups'
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    id    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user  = models.ForeignKey(User,  on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="Пользователь"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name="Группа"
    )
    class Meta:
        db_table       = 'group_members'
        unique_together = ('user', 'group')
        verbose_name = 'Участник группы'
        verbose_name_plural = 'Участники групп'

    def __str__(self):
        return f"{self.user} in {self.group}"


# Новая модель для связи преподавателей с группами
class TeacherGroup(models.Model):
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_groups',
        limit_choices_to={'role': 'teacher'}, # Ограничиваем выбор только преподавателями
        verbose_name="Преподаватель"
    )
    group   = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='group_teachers',
        verbose_name="Группа"
    )

    class Meta:
        db_table = 'teacher_groups'
        unique_together = ('teacher', 'group')
        verbose_name = 'Преподаватель группы'
        verbose_name_plural = 'Преподаватели групп'

    def __str__(self):
        return f"{self.teacher.firstname} {self.teacher.lastname} in {self.group.name}"


# ═══════════════════════════════════════════════════════════════════════
# VIDEO
# ═══════════════════════════════════════════════════════════════════════

class VideoType(models.Model):
    id   = models.BigAutoField("ИД типа видео",primary_key=True)
    name = models.CharField("Название типа видео",max_length=100, unique=True)

    class Meta:
        db_table = 'video_types'
        verbose_name = 'Тип видео'
        verbose_name_plural = 'Типы видео'

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
        verbose_name = 'Видео'
        verbose_name_plural = 'Видео'

    def __str__(self):
        return f"{self.name} ({self.type})"



# ═══════════════════════════════════════════════════════════════════════
# CONTENT STRUCTURE
# ═══════════════════════════════════════════════════════════════════════

class Subject(models.Model):
    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Название предмета", max_length=255)
    # Новое поле для отслеживания создателя предмета
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_subjects',
        verbose_name="Создатель"
    )

    class Meta:
        db_table = 'subjects'
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'

    def __str__(self):
        return self.name


# Новая модель для связи предметов с группами
class GroupSubject(models.Model):
    id      = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group   = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='group_subjects',
        verbose_name="Группа"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='subject_groups',
        verbose_name="Предмет"
    )

    class Meta:
        db_table = 'group_subjects'
        unique_together = ('group', 'subject')
        verbose_name = 'Предмет группы'
        verbose_name_plural = 'Предметы групп'

    def __str__(self):
        return f"{self.subject.name} for {self.group.name}"


class Block(models.Model):
    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ИД блока")
    subject        = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='blocks', help_text='Предмет, в котором находится блок', verbose_name="Предмет")
    title          = models.CharField(max_length=255, verbose_name="Заголовок блока")
    final_test     = models.OneToOneField(
        'Test', on_delete=models.SET_NULL, null=True, blank=True, related_name='final_block_of',help_text='Финальный тест в конце блока ', verbose_name="Финальный тест блока"
    )
    lessons_count  = models.IntegerField(default=0, verbose_name="Кол-во уроков в блоке")
    description    = models.TextField(blank=True, null=True, verbose_name="Описание блока")
    position       = models.IntegerField(default=0, help_text='Влияет на порядок обьектов ',verbose_name="Позиция блока в уроке")
    is_published   = models.BooleanField(default=False, help_text='Видимость для пользователей ', verbose_name="Опубликовано?")

    class Meta:
        db_table = 'blocks'
        ordering = ['position']
        verbose_name = 'Блок'
        verbose_name_plural = 'Блоки'

    def __str__(self):
        return f"{self.title} ({self.subject.name})"


class Lesson(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ИД Урока")
    block        = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='lessons', help_text='Блок в котором находится урок ', verbose_name="Блок")
    test         = models.OneToOneField(
        'Test', on_delete=models.SET_NULL, null=True, blank=True, related_name='lesson_for', help_text='Тест в уроке ',verbose_name="Тест"
    )
    # ── видео ──
    video        = models.ForeignKey(
        Video, on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons',
        help_text='Видеоматериал урока', verbose_name="Связанное видео"
    )
    title        = models.CharField(max_length=255, blank=True, null=True, verbose_name="Заголовок")
    summary      = models.CharField(max_length=1000, blank=True, null=True, verbose_name="Саммари урока")
    duration     = models.IntegerField(default=0, help_text='Суммарная длительность урока в секундах', verbose_name="Длительность")
    position     = models.IntegerField(default=0, help_text='Влияет на порядок обьектов ', verbose_name="Позиция урока")
    is_published = models.BooleanField(default=False, help_text='Видимость для пользователей ', verbose_name="Опубликовано?")

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
    id           = models.BigAutoField(primary_key=True, verbose_name="ИД Теста")
    title        = models.CharField(max_length=255, help_text='Название', verbose_name="Заголовок теста")
    description  = models.TextField(blank=True, null=True, verbose_name="Описание теста")
    duration     = models.IntegerField(default=0, help_text='Таймер теста в секундах (0 = без ограничений)', verbose_name="Длительность теста в сек")
    is_published = models.BooleanField(default=False, help_text='Видимость для пользователей ', verbose_name="Опубликовано?")

    class Meta:
        db_table = 'tests'
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return self.title


class Question(models.Model):
    id                       = models.BigAutoField(primary_key=True)
    text                     = models.TextField(verbose_name="Текст вопроса")
    test                     = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions', verbose_name="Связанный тест")
    recommendation_link      = models.URLField(
        max_length=2048, null=True, blank=True,
        help_text='Материал для повторения по этому вопросу'
        , verbose_name="Ссылка на текстовую рекомендацию"
    )
    recommendation_video_link = models.URLField(
        max_length=2048, null=True, blank=True,
        help_text='Материал для повторения по этому вопросу'
        , verbose_name="Ссылка на видео ресурс"
    )

    class Meta:
        db_table = 'questions'
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return self.text[:50] + "..."


class Answer(models.Model):
    id         = models.BigAutoField(primary_key=True)
    text       = models.TextField(verbose_name="Текст ответа")
    is_correct = models.BooleanField(verbose_name="Правильно?")
    question   = models.ForeignKey(Question, on_delete=models.CASCADE,
                                   related_name='answers', null=True, blank=True, verbose_name="Связанный вопрос")

    class Meta:
        db_table = 'answers'
        verbose_name = "Ответ"
        verbose_name_plural = 'Ответы'

    def __str__(self):
        return f"Answer for Q{self.question_id}: {'✓' if self.is_correct else '✗'}"


# ═══════════════════════════════════════════════════════════════════════
# TEST RESULTS
# ═══════════════════════════════════════════════════════════════════════

class TestResult(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ИД Результата")
    score        = models.IntegerField(verbose_name="Оценка")
    started_at   = models.DateTimeField(verbose_name="Начало в")
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="Конец в")
    user         = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name='results', null=True, blank=True, verbose_name="Пользователь")
    test         = models.ForeignKey(Test, on_delete=models.CASCADE,
                                     related_name='results', null=True, blank=True, verbose_name="Тест")

    class Meta:
        db_table = 'test_results'
        verbose_name = "Результаты тестирования"
        verbose_name_plural = 'Результаты тестирований'

    def __str__(self):
        return f"{self.user} — {self.test} — {self.score}"


# ═══════════════════════════════════════════════════════════════════════
# TRAINER
# ═══════════════════════════════════════════════════════════════════════

class UserAnswer(models.Model):

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ИД ответа пользователя")
    test_result    = models.ForeignKey(TestResult, on_delete=models.CASCADE,
                                       related_name='user_answers', verbose_name="ИД результата тестирования")
    question       = models.ForeignKey(Question, on_delete=models.CASCADE,
                                       related_name='user_answers', verbose_name="Вопрос")
    chosen_answer  = models.ForeignKey(Answer, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='chosen_in', verbose_name="Выбранный ответ")
    is_correct     = models.BooleanField(default=False, verbose_name="Правильность")
    answered_at    = models.DateTimeField(auto_now_add=True, verbose_name="Отвечено в")

    class Meta:
        db_table       = 'user_answers'
        unique_together = ('test_result', 'question')   # один ответ на вопрос за попытку
        indexes         = [
            models.Index(fields=['test_result', 'is_correct']),  # быстрый поиск ошибок попытки
        ]
        verbose_name = "Ответ пользователя"
        verbose_name_plural = 'Ответы пользователей'

    def __str__(self):
        mark = '✓' if self.is_correct else '✗'
        return f"{self.test_result_id} | Q{self.question_id} [{mark}]"


class TrainingSession(models.Model):

    STATUS_CHOICES = [
        ('pending',    'Не начата'),
        ('active',     'В процессе'),
        ('completed',  'Завершена'),
    ]

    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ИД Сессии тренажера")
    user               = models.ForeignKey(User, on_delete=models.CASCADE,
                                           related_name='training_sessions', verbose_name="Пользователь")
    lesson             = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                                           null=True, blank=True, related_name='training_sessions',
                                           help_text='Урок, к которому относится сессия тренажёра', verbose_name="Урок")
    status             = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    source_test_result = models.ForeignKey(TestResult, on_delete=models.SET_NULL,
                                           null=True, blank=True,
                                           related_name='training_sessions',
                                           help_text='Попытка, по ошибкам которой создана сессия. '
                                                     'null = глобальный тренажёр', verbose_name="Попытка теста")
    created_at         = models.DateTimeField(auto_now_add=True, verbose_name="Создана в")
    completed_at       = models.DateTimeField(null=True, blank=True, verbose_name="Пройдена в")

    class Meta:
        db_table = 'training_sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'lesson', 'status']),  # быстрый поиск активных сессий по уроку
        ]
        verbose_name = "Сессия тренажера"
        verbose_name_plural = "Сессии тренажера"

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

    id             = models.BigAutoField(primary_key=True, verbose_name="ИД Вопрсоа тренажера")
    session        = models.ForeignKey(TrainingSession, on_delete=models.CASCADE,
                                       related_name='training_questions', verbose_name="Сессия")
    question       = models.ForeignKey(Question, on_delete=models.CASCADE,
                                       related_name='training_questions', verbose_name="Вопрос")
    chosen_answer  = models.ForeignKey(Answer, on_delete=models.SET_NULL,
                                       null=True, blank=True,
                                       related_name='chosen_in_training', verbose_name="Выбранный ответ")
    is_correct     = models.BooleanField(null=True, blank=True, verbose_name="Правильность")   # null = ещё не отвечено
    position       = models.IntegerField(default=0, verbose_name="Позиция")
    status         = models.CharField(max_length=8, choices=STATUS_CHOICES, default='pending', verbose_name="Статус прохождения")
    answered_at    = models.DateTimeField(null=True, blank=True, verbose_name="Отвечено в")

    class Meta:
        db_table       = 'training_questions'
        unique_together = ('session', 'question')
        ordering        = ['position']
        verbose_name = "Вопрос тренажера"
        verbose_name_plural = "Вопросы тренажера"

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