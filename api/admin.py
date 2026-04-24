from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.hashers import make_password
from .models import (
    User, Group, GroupMember, Subject, Block,
    Lesson, Test, Question, Answer, Video, TestResult, VideoType, UserAnswer,
    TrainingSession, TrainingQuestion
)

# Настройки заголовков админ-панели
admin.site.site_header = "Учебная платформа — Администрирование"
admin.site.site_title = "Админ-панель"
admin.site.index_title = "Управление контентом и пользователями"


def has_admin_permission(user):
    """Проверка прав администратора"""
    return hasattr(user, 'role') and user.role == 'admin'


def has_teacher_permission(user):
    """Проверка прав преподавателя или администратора"""
    return hasattr(user, 'role') and user.role in ['teacher', 'admin']


class UserAnswerInline(admin.TabularInline):
    """Отображение ответов пользователя внутри результата теста (только чтение)."""
    model = UserAnswer
    readonly_fields = ('question', 'chosen_answer', 'is_correct', 'answered_at')
    extra = 0
    can_delete = False
    verbose_name = "Ответ пользователя"
    verbose_name_plural = "Детализация ответов"

    def has_add_permission(self, request, obj=None):
        return False


class AnswerInline(admin.TabularInline):
    """Редактирование вариантов ответов прямо внутри вопроса."""
    model = Answer
    extra = 4
    verbose_name = "Вариант ответа"
    verbose_name_plural = "Варианты ответов"
    fields = ('text', 'is_correct')


class TrainingQuestionInline(admin.TabularInline):
    """Отображение вопросов внутри сессии тренажёра (только чтение)."""
    model = TrainingQuestion
    readonly_fields = ('question', 'status', 'is_correct', 'chosen_answer', 'position')
    extra = 0
    can_delete = False
    verbose_name = "Вопрос тренажёра"
    verbose_name_plural = "Вопросы в сессии"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Управление пользователями платформы."""
    list_display = ('email', 'lastname', 'firstname', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'lastname', 'firstname')
    ordering = ('lastname', 'firstname')
    fieldsets = (
        ('Личная информация', {'fields': ('firstname', 'lastname', 'patronymic', 'email')}),
        ('Настройки доступа', {'fields': ('role', 'is_active', 'is_staff')}),
    )
    verbose_name = "Пользователь"
    verbose_name_plural = "Пользователи"
    
    def has_add_permission(self, request):
        # Админы и преподаватели могут добавлять пользователей
        return has_teacher_permission(request.user)
    
    def has_change_permission(self, request, obj=None):
        # Админы могут менять всех, преподаватели - только студентов
        if has_admin_permission(request.user):
            return True
        if request.user.role == 'teacher' and obj:
            return obj.role != 'admin'  # Преподаватель не может менять админов
        return has_teacher_permission(request.user)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request.user)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Управление учебными группами. Доступно для просмотра всем преподавателям и админам."""
    list_display = ('name', 'members_count')
    search_fields = ('name',)
    
    def members_count(self, obj):
        return obj.members.count()
    members_count.short_description = "Участников"
    verbose_name = "Группа"
    verbose_name_plural = "Группы"
    
    def has_view_permission(self, request, obj=None):
        # Преподаватели и админы могут видеть группы
        return has_teacher_permission(request.user)
    
    def has_change_permission(self, request, obj=None):
        # Только админы могут изменять группы
        return has_admin_permission(request.user)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request.user)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    """Связь пользователей с группами."""
    list_display = ('user', 'group')
    list_filter = ('group',)
    autocomplete_fields = ('user', 'group')
    verbose_name = "Участник группы"
    verbose_name_plural = "Участники групп"


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Управление учебными предметами. Доступно преподавателям и админам."""
    list_display = ('name', 'blocks_count', 'lessons_count')
    search_fields = ('name',)
    ordering = ('name',)
    
    def blocks_count(self, obj):
        return obj.blocks.count()
    blocks_count.short_description = "Блоков"
    
    def lessons_count(self, obj):
        return sum(block.lessons.count() for block in obj.blocks.all())
    lessons_count.short_description = "Уроков"
    verbose_name = "Предмет"
    verbose_name_plural = "Предметы"
    
    def has_view_permission(self, request, obj=None):
        return has_teacher_permission(request.user)
    
    def has_change_permission(self, request, obj=None):
        return has_teacher_permission(request.user)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request.user)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    """Управление тематическими блоками внутри предмета. Доступно преподавателям и админам."""
    list_display = ('title', 'subject', 'position', 'lessons_count', 'is_published')
    list_filter = ('subject', 'is_published')
    list_editable = ('position', 'is_published')
    search_fields = ('title', 'subject__name')
    ordering = ('subject', 'position')
    fieldsets = (
        ('Основная информация', {'fields': ('title', 'subject', 'description')}),
        ('Настройки отображения', {'fields': ('position', 'is_published')}),
        ('Итоговый тест', {'fields': ('final_test',), 'description': 'Тест для проверки знаний по всему блоку'}),
    )
    
    def lessons_count(self, obj):
        return obj.lessons.count()
    lessons_count.short_description = "Уроков"
    verbose_name = "Тематический блок"
    verbose_name_plural = "Тематические блоки"
    
    def has_view_permission(self, request, obj=None):
        return has_teacher_permission(request.user)
    
    def has_change_permission(self, request, obj=None):
        return has_teacher_permission(request.user)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request.user)


@admin.register(VideoType)
class VideoTypeAdmin(admin.ModelAdmin):
    """
    Управление типами видео (например: 'Лекция', 'Практика', 'Вебинар').
    Позволяет классифицировать видеоматериалы для удобного поиска.
    Доступно администраторам и преподавателям (только просмотр).
    """
    list_display = ('name', 'videos_count')
    search_fields = ('name',)
    ordering = ('name',)
    
    def videos_count(self, obj):
        """
        Подсчитывает количество видео данного типа.
        """
        return Video.objects.filter(type=obj).count()
    
    videos_count.short_description = "Количество видео"
    verbose_name = "Тип видео"
    verbose_name_plural = "Типы видео"
    
    def has_view_permission(self, request, obj=None):
        # Админы и преподаватели могут видеть типы видео
        return has_teacher_permission(request.user)
    
    def has_change_permission(self, request, obj=None):
        # Только админы могут изменять типы видео
        return has_admin_permission(request.user)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request.user)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Управление видеоматериалами (загрузка файла или ссылка). Доступно преподавателям и админам."""
    list_display = ('name', 'type', 'duration', 'link_preview', 'open_video', 'file_or_link')
    list_filter = ('type',)
    search_fields = ('name', 'description', 'link')
    ordering = ('-id',)
    fieldsets = (
        ('Основная информация', {'fields': ('name', 'description', 'type', 'duration'), 'description': 'Название, описание и тип видео'}),
        ('Источник видео', {'fields': ('video_file', 'link'), 'description': 'Загрузите файл или укажите ссылку (Rutube, YouTube и др.)'}),
    )
    
    def link_preview(self, obj):
        return (obj.link[:40] + "...") if obj.link and len(obj.link) > 40 else (obj.link or "—")
    link_preview.short_description = "Ссылка"
    
    def open_video(self, obj):
        url = obj.get_video_url()
        if url:
            return format_html('<a class="button" href="{}" target="_blank" style="background-color: #28a745; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none;">▶ Смотреть</a>', url)
        return format_html('<span style="color: #999;">Нет видео</span>')
    open_video.short_description = "Просмотр"
    
    def file_or_link(self, obj):
        if obj.video_file:
            return format_html('<span style="color: green;">✓ Файл</span>')
        elif obj.link:
            return format_html('<span style="color: blue;">✓ Ссылка</span>')
        return format_html('<span style="color: red;">✗ Нет</span>')
    file_or_link.short_description = "Источник"
    verbose_name = "Видео"
    verbose_name_plural = "Видеоматериалы"
    
    def has_view_permission(self, request, obj=None):
        # Преподаватели и админы могут видеть видео
        return has_teacher_permission(request.user)
    
    def has_change_permission(self, request, obj=None):
        # Преподаватели и админы могут изменять видео
        return has_teacher_permission(request.user)
    
    def has_delete_permission(self, request, obj=None):
        # Только админы могут удалять видео
        return has_admin_permission(request.user)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Управление уроками (видео, тест, краткое содержание). Доступно преподавателям и админам."""
    list_display = ('title', 'block', 'position', 'duration', 'video_details', 'is_published')
    list_filter = ('block', 'block__subject', 'is_published')
    list_editable = ('position', 'duration', 'is_published')
    search_fields = ('title', 'summary', 'block__title')
    ordering = ('block', 'position')
    fieldsets = (
        ('Основная информация', {'fields': ('title', 'block', 'summary'), 'description': 'Название урока, принадлежность к блоку и краткое описание'}),
        ('Медиа-контент', {'fields': ('video',), 'description': 'Выберите видео для этого урока из загруженных ранее'}),
        ('Тестирование', {'fields': ('test',), 'description': 'Тест для проверки знаний по уроку (необязательно)'}),
        ('Настройки отображения', {'fields': ('position', 'duration', 'is_published'), 'description': 'Позиция в блоке, длительность в секундах, статус публикации'}),
    )
    
    def video_details(self, obj):
        if obj.video:
            v = obj.video
            v_type = v.type.name if hasattr(v.type, 'name') else str(v.type)
            link_display = (v.link[:20] + '...') if v.link and len(v.link) > 20 else (v.link or '—')
            return format_html('<span style="font-size: 11px; line-height: 1.4;"><b>Тип:</b> {}<br><b>Длительность:</b> {} сек.<br><b>Ссылка:</b> <span style="color: #666;">{}</span></span>', v_type, v.duration, link_display)
        return format_html('<span style="color: #999; font-style: italic;">Видео не привязано</span>')
    video_details.short_description = "Параметры видео"
    verbose_name = "Урок"
    verbose_name_plural = "Уроки"
    
    def has_view_permission(self, request, obj=None):
        return has_teacher_permission(request.user)
    
    def has_change_permission(self, request, obj=None):
        return has_teacher_permission(request.user)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request.user)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    """Управление тестами (прикреплённые к урокам или итоговые для блоков). Доступно преподавателям и админам."""
    list_display = ('title', 'duration', 'questions_count', 'is_published', 'used_in')
    list_filter = ('is_published',)
    list_editable = ('is_published',)
    search_fields = ('title', 'description')
    ordering = ('-id',)
    fieldsets = (
        ('Основная информация', {'fields': ('title', 'description'), 'description': 'Название и описание теста'}),
        ('Настройки', {'fields': ('duration', 'is_published'), 'description': 'Длительность в секундах (0 = без ограничений), статус публикации'}),
    )
    
    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = "Вопросов"
    
    def used_in(self, obj):
        parts = []
        if hasattr(obj, 'lesson_for') and obj.lesson_for:
            parts.append(f"Урок: {obj.lesson_for.title}")
        if hasattr(obj, 'final_block_of') and obj.final_block_of:
            parts.append(f"Блок: {obj.final_block_of.title}")
        return ", ".join(parts) if parts else "Не используется"
    used_in.short_description = "Используется в"
    verbose_name = "Тест"
    verbose_name_plural = "Тесты"
    
    def has_view_permission(self, request, obj=None):
        return has_teacher_permission(request.user)
    
    def has_change_permission(self, request, obj=None):
        return has_teacher_permission(request.user)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request.user)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Управление вопросами тестов (с вариантами ответов и рекомендациями). Доступно преподавателям и админам."""
    list_display = ('text_preview', 'test', 'has_recommendations')
    list_filter = ('test', 'test__is_published')
    search_fields = ('text',)
    inlines = [AnswerInline]
    ordering = ('test', 'id')
    fieldsets = (
        ('Текст вопроса', {'fields': ('text', 'test'), 'description': 'Формулировка вопроса и принадлежность к тесту'}),
        ('Материалы для повторения', {'fields': ('recommendation_link', 'recommendation_video_link'), 'description': 'Ссылки на материалы для работы над ошибками', 'classes': ('collapse',)}),
    )
    
    def text_preview(self, obj):
        return (obj.text[:60] + "...") if len(obj.text) > 60 else obj.text
    text_preview.short_description = "Вопрос"
    
    def has_recommendations(self, obj):
        return format_html('<span style="color: green;">✓ Есть</span>') if obj.recommendation_link or obj.recommendation_video_link else format_html('<span style="color: #999;">✗ Нет</span>')
    has_recommendations.short_description = "Рекомендации"
    verbose_name = "Вопрос"
    verbose_name_plural = "Вопросы"
    
    def has_view_permission(self, request, obj=None):
        return has_teacher_permission(request.user)
    
    def has_change_permission(self, request, obj=None):
        return has_teacher_permission(request.user)
    
    def has_delete_permission(self, request, obj=None):
        return has_admin_permission(request.user)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    """Просмотр результатов тестирования пользователей (только чтение)."""
    list_display = ('user', 'test', 'score_colored', 'correct_answers_count', 'completed_at')
    readonly_fields = ('user', 'test', 'score', 'started_at', 'completed_at')
    list_filter = ('test', 'user', 'completed_at')
    ordering = ('-completed_at',)
    inlines = [UserAnswerInline]
    
    def score_colored(self, obj):
        if obj.score >= 80:
            color, label = "green", "Отлично"
        elif obj.score >= 50:
            color, label = "orange", "Нормально"
        else:
            color, label = "red", "Плохо"
        return format_html('<b style="color: {}; font-size: 13px;">{}% ({})</b>', color, obj.score, label)
    score_colored.short_description = "Результат"
    
    def correct_answers_count(self, obj):
        count = UserAnswer.objects.filter(test_result=obj, is_correct=True).count()
        total = UserAnswer.objects.filter(test_result=obj).count()
        return f"{count} из {total}"
    correct_answers_count.short_description = "Верных ответов"
    verbose_name = "Результат теста"
    verbose_name_plural = "Результаты тестов"


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    """Общий список всех ответов пользователей (для анализа ошибок)."""
    list_display = ('user_email', 'test_name', 'question_text', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'answered_at', 'test_result__test')
    ordering = ('-answered_at',)
    search_fields = ('test_result__user__email', 'question__text')
    
    def user_email(self, obj):
        return obj.test_result.user.email if obj.test_result.user else "Аноним"
    user_email.short_description = "Пользователь"
    
    def test_name(self, obj):
        return obj.test_result.test.title if obj.test_result.test else "—"
    test_name.short_description = "Тест"
    
    def question_text(self, obj):
        return (obj.question.text[:50] + "...") if len(obj.question.text) > 50 else obj.question.text
    question_text.short_description = "Вопрос"
    verbose_name = "Ответ пользователя"
    verbose_name_plural = "Все ответы пользователей"


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    """Управление сессиями тренажёра для работы над ошибками (автоматическое)."""
    list_display = ('user', 'lesson_info', 'status', 'questions_count', 'created_at', 'completed_at')
    list_filter = ('status', 'lesson', 'lesson__block__subject')
    readonly_fields = ('user', 'lesson', 'status', 'source_test_result', 'created_at', 'completed_at')
    ordering = ('-created_at',)
    inlines = [TrainingQuestionInline]
    search_fields = ('user__email', 'lesson__title')
    
    def lesson_info(self, obj):
        return f"{obj.lesson.title} ({obj.lesson.block.subject.name})" if obj.lesson else "Общий тренажёр"
    lesson_info.short_description = "Урок"
    
    def questions_count(self, obj):
        return obj.training_questions.count()
    questions_count.short_description = "Вопросов"
    verbose_name = "Сессия тренажёра"
    verbose_name_plural = "Сессии тренажёра"


@admin.register(TrainingQuestion)
class TrainingQuestionAdmin(admin.ModelAdmin):
    """Вопросы внутри сессий тренажёра (автоматическое управление)."""
    list_display = ('session_id_short', 'question_text', 'status', 'is_correct', 'answered_at')
    list_filter = ('status', 'session__lesson', 'session__lesson__block__subject')
    readonly_fields = ('session', 'question', 'chosen_answer', 'is_correct', 'position', 'status', 'answered_at')
    ordering = ('session', 'position')
    search_fields = ('question__text',)
    
    def session_id_short(self, obj):
        return str(obj.session.id)[:8] + "..."
    session_id_short.short_description = "Сессия"
    
    def question_text(self, obj):
        return (obj.question.text[:50] + "...") if len(obj.question.text) > 50 else obj.question.text
    question_text.short_description = "Вопрос"
    verbose_name = "Вопрос тренажёра"
    verbose_name_plural = "Вопросы тренажёра"
