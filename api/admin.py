from django.contrib import admin
from django.contrib.auth.models import Group as AuthGroup
from django.utils.html import format_html
from django.contrib.admin import AdminSite as _AdminSite
import logging
from django.conf import settings
from .models import (
    User, Group, GroupMember, Subject, Block,
    Lesson, Test, Question, Answer, Video, TestResult, VideoType, UserAnswer,
    TrainingSession, TrainingQuestion
)

# ──────────────────────────────────────────────────────────────────────────────
# Убираем стандартную модель Groups из Django Auth.
# У нас есть собственная модель api.Group — встроенная только путает.
# ──────────────────────────────────────────────────────────────────────────────
try:
    admin.site.unregister(AuthGroup)
except admin.sites.NotRegistered:
    pass

admin.site.site_header = "Учебная платформа — Администрирование"
admin.site.site_title  = "Edu Platform"
admin.site.index_title = "Панель управления"

_orig_index = _AdminSite.index
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ПРОВЕРКИ ПРАВ
# ══════════════════════════════════════════════════════════════════════════════

def is_admin(user):
    """Только роль 'admin'."""
    return hasattr(user, 'role') and user.role == 'admin'

def is_teacher_or_admin(user):
    """Роль 'teacher' или 'admin'."""
    return hasattr(user, 'role') and user.role in ('teacher', 'admin')


# ══════════════════════════════════════════════════════════════════════════════
# INLINE-КЛАССЫ
# ══════════════════════════════════════════════════════════════════════════════

class AnswerInline(admin.TabularInline):
    """Варианты ответов внутри вопроса (для преподавателей — редактируемые)."""
    model   = Answer
    extra   = 4
    verbose_name        = "Вариант ответа"
    verbose_name_plural = "Варианты ответов"
    fields  = ('text', 'is_correct')


class UserAnswerInline(admin.TabularInline):
    """Детализация ответов внутри результата теста — только чтение."""
    model          = UserAnswer
    readonly_fields = ('question', 'chosen_answer', 'is_correct', 'answered_at')
    extra          = 0
    can_delete     = False
    verbose_name        = "Ответ"
    verbose_name_plural = "Детализация ответов"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class TrainingQuestionInline(admin.TabularInline):
    """Вопросы внутри сессии тренажёра — только чтение."""
    model          = TrainingQuestion
    readonly_fields = ('question', 'status', 'is_correct', 'chosen_answer', 'position')
    extra          = 0
    can_delete     = False
    verbose_name        = "Вопрос"
    verbose_name_plural = "Вопросы в сессии"

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class GroupMemberInline(admin.TabularInline):
    """Участники прямо внутри карточки группы."""
    model              = GroupMember
    extra              = 1
    autocomplete_fields = ('user',)
    verbose_name        = "Участник"
    verbose_name_plural = "Состав группы"


# ══════════════════════════════════════════════════════════════════════════════
# ░░░░░░░░░░░░░░░░░  РАЗДЕЛ: ОБУЧЕНИЕ  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# Иерархия: Предметы → Блоки → Уроки → Тесты → Вопросы → Ответы
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Учебные предметы (Математика, Физика…)."""
    list_display   = ('name', 'blocks_count', 'lessons_count')
    search_fields  = ('name',)
    ordering       = ('name',)

    def blocks_count(self, obj):
        return obj.blocks.count()
    blocks_count.short_description = "Блоков"

    def lessons_count(self, obj):
        return sum(b.lessons.count() for b in obj.blocks.all())
    lessons_count.short_description = "Уроков"

    # Права
    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_teacher_or_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_teacher_or_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    """Тематические блоки внутри предмета (Алгебра, Геометрия…)."""
    list_display   = ('title', 'subject', 'position', 'lessons_count', 'is_published')
    list_filter    = ('subject', 'is_published')
    list_editable  = ('position', 'is_published')
    search_fields  = ('title', 'subject__name')
    ordering       = ('subject', 'position')
    fieldsets = (
        ('Основная информация', {'fields': ('title', 'subject', 'description')}),
        ('Настройки',          {'fields': ('position', 'is_published')}),
        ('Итоговый тест',      {'fields': ('final_test',),
                                'description': 'Тест для проверки знаний по всему блоку'}),
    )

    def lessons_count(self, obj):
        return obj.lessons.count()
    lessons_count.short_description = "Уроков"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_teacher_or_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_teacher_or_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Уроки: видеоматериал + тест + краткое содержание."""
    list_display   = ('title', 'block', 'position', 'duration', 'video_info', 'is_published')
    list_filter    = ('block', 'block__subject', 'is_published')
    list_editable  = ('position', 'duration', 'is_published')
    search_fields  = ('title', 'summary', 'block__title')
    ordering       = ('block', 'position')
    fieldsets = (
        ('Основная информация',    {'fields': ('title', 'block', 'summary')}),
        ('Медиа-контент',          {'fields': ('video',)}),
        ('Тестирование',           {'fields': ('test',)}),
        ('Настройки отображения',  {'fields': ('position', 'duration', 'is_published')}),
    )

    def video_info(self, obj):
        if not obj.video:
            return format_html('<span style="color:#aaa; font-style:italic;">Нет видео</span>')
        v    = obj.video
        vtype = v.type.name if hasattr(v.type, 'name') else str(v.type)
        link  = (v.link[:22] + '…') if v.link and len(v.link) > 22 else (v.link or '—')
        return format_html(
            '<span style="font-size:11px; line-height:1.5;">'
            '<b>Тип:</b> {}<br><b>Длит.:</b> {} сек.<br>'
            '<span style="color:#666;">{}</span></span>',
            vtype, v.duration, link,
        )
    video_info.short_description = "Видео"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_teacher_or_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_teacher_or_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    """Тесты (привязаны к уроку или служат итоговым для блока)."""
    list_display   = ('title', 'duration_fmt', 'questions_count', 'is_published', 'used_in')
    list_filter    = ('is_published',)
    list_editable  = ('is_published',)
    search_fields  = ('title', 'description')
    ordering       = ('-id',)
    fieldsets = (
        ('Основная информация', {'fields': ('title', 'description')}),
        ('Настройки', {
            'fields': ('duration', 'is_published'),
            'description': 'Длительность в секундах (0 = без ограничения)',
        }),
    )

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = "Вопросов"

    def duration_fmt(self, obj):
        if not obj.duration:
            return '∞ Без лимита'
        m, s = divmod(obj.duration, 60)
        return f'{m} мин {s} сек' if m else f'{s} сек'
    duration_fmt.short_description = "Длительность"

    def used_in(self, obj):
        parts = []
        if hasattr(obj, 'lesson_for') and obj.lesson_for:
            parts.append(f"📖 Урок: {obj.lesson_for.title}")
        if hasattr(obj, 'final_block_of') and obj.final_block_of:
            parts.append(f"📦 Блок: {obj.final_block_of.title}")
        return ", ".join(parts) if parts else format_html('<span style="color:#aaa;">—</span>')
    used_in.short_description = "Используется в"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_teacher_or_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_teacher_or_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Вопросы тестов.
    Варианты ответов редактируются прямо здесь через inline.
    """
    list_display   = ('text_preview', 'test', 'answers_count', 'has_recommendations')
    list_filter    = ('test', 'test__is_published')
    search_fields  = ('text',)
    inlines        = [AnswerInline]
    ordering       = ('test', 'id')
    fieldsets = (
        ('Текст вопроса', {'fields': ('text', 'test')}),
        ('Материалы для повторения', {
            'fields': ('recommendation_link', 'recommendation_video_link'),
            'classes': ('collapse',),
            'description': 'Ссылки на материалы для работы над ошибками',
        }),
    )

    def text_preview(self, obj):
        t = obj.text
        return (t[:75] + '…') if len(t) > 75 else t
    text_preview.short_description = "Вопрос"

    def answers_count(self, obj):
        total   = obj.answers.count()
        correct = obj.answers.filter(is_correct=True).count()
        color   = 'green' if correct == 1 else ('orange' if correct == 0 else '#dc3545')
        return format_html(
            '{} вар. &nbsp;<span style="color:{}; font-size:11px;">({} верных)</span>',
            total, color, correct,
        )
    answers_count.short_description = "Ответы"

    def has_recommendations(self, obj):
        if obj.recommendation_link or obj.recommendation_video_link:
            return format_html('<span style="color:green;">✓ Есть</span>')
        return format_html('<span style="color:#ccc;">✗ Нет</span>')
    has_recommendations.short_description = "Рекомендации"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_teacher_or_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_teacher_or_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Варианты ответов — отдельный список для полного контроля.
    Преподаватели видят ответы в readonly (чтобы не испортить тесты).
    Добавление/изменение — только через QuestionAdmin → inline или администратором.
    """
    list_display   = ('text_preview', 'question_preview', 'is_correct_badge')
    list_filter    = ('is_correct', 'question__test')
    search_fields  = ('text', 'question__text')
    ordering       = ('question', 'id')
    fieldsets = (
        ('Вариант ответа', {'fields': ('question', 'text', 'is_correct')}),
    )

    def text_preview(self, obj):
        t = obj.text
        return (t[:65] + '…') if len(t) > 65 else t
    text_preview.short_description = "Текст ответа"

    def question_preview(self, obj):
        t = obj.question.text
        return (t[:55] + '…') if len(t) > 55 else t
    question_preview.short_description = "Вопрос"

    def is_correct_badge(self, obj):
        if obj.is_correct:
            return format_html(
                '<span style="background:#28a745; color:#fff; padding:2px 10px; '
                'border-radius:12px; font-size:12px;">✓ Верный</span>'
            )
        return format_html(
            '<span style="background:#e9ecef; color:#6c757d; padding:2px 10px; '
            'border-radius:12px; font-size:12px;">✗ Неверный</span>'
        )
    is_correct_badge.short_description = "Правильный?"

    # Права: просмотр — преподаватели; изменение/удаление — только администраторы
    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)

    def get_readonly_fields(self, request, obj=None):
        # Преподаватель видит форму, но всё в readonly
        if not is_admin(request.user):
            return [f.name for f in self.model._meta.fields]
        return ()


# ══════════════════════════════════════════════════════════════════════════════
# ░░░░░░░░░░░░░░░░  РАЗДЕЛ: ПОЛЬЗОВАТЕЛИ  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Пользователи платформы.
    • Администратор — полный CRUD, включая смену роли.
    • Преподаватель — только просмотр (все поля readonly).
    """
    list_display   = ('email', 'full_name', 'role_badge', 'is_active', 'is_staff')
    list_filter    = ('role', 'is_active', 'is_staff')
    search_fields  = ('email', 'lastname', 'firstname')
    ordering       = ('lastname', 'firstname')
    fieldsets = (
        ('Личная информация', {'fields': ('firstname', 'lastname', 'patronymic', 'email')}),
        ('Настройки доступа', {'fields': ('role', 'is_active', 'is_staff')}),
    )

    def full_name(self, obj):
        name = f"{obj.lastname} {obj.firstname}".strip()
        return name or obj.email
    full_name.short_description = "ФИО"

    def role_badge(self, obj):
        cfg = {
            'admin':   ('#dc3545', '👑 Админ'),
            'teacher': ('#28a745', '🎓 Преподаватель'),
            'student': ('#007bff', '📖 Студент'),
        }
        color, label = cfg.get(obj.role, ('#666', obj.role))
        return format_html(
            '<span style="color:{}; font-weight:600;">{}</span>', color, label
        )
    role_badge.short_description = "Роль"

    def has_view_permission(self, request, obj=None):
        return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):
        # Только администратор создаёт пользователей
        return is_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return is_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_admin(request.user)

    def get_readonly_fields(self, request, obj=None):
        if not is_admin(request.user):
            return [f.name for f in self.model._meta.fields]
        return ()


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Учебные группы с inline-списком участников."""
    list_display   = ('name', 'members_count')
    search_fields  = ('name',)
    inlines        = [GroupMemberInline]

    def members_count(self, obj):
        return obj.members.count()
    members_count.short_description = "Участников"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    """Участники групп — отдельный список для массовых операций."""
    list_display        = ('user', 'group')
    list_filter         = ('group',)
    autocomplete_fields = ('user', 'group')

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


# ══════════════════════════════════════════════════════════════════════════════
# ░░░░░░░░░░░░░░░░░░░  РАЗДЕЛ: ВИДЕО  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Видеоматериалы: загрузка файла или внешняя ссылка (Rutube / YouTube)."""
    list_display   = ('name', 'type', 'duration_fmt', 'source_badge', 'open_video')
    list_filter    = ('type',)
    search_fields  = ('name', 'description', 'link')
    ordering       = ('-id',)
    fieldsets = (
        ('Основная информация', {'fields': ('name', 'description', 'type', 'duration')}),
        ('Источник видео', {
            'fields': ('video_file', 'link'),
            'description': 'Загрузите файл или укажите внешнюю ссылку',
        }),
    )

    def duration_fmt(self, obj):
        if not obj.duration:
            return '—'
        m, s = divmod(obj.duration, 60)
        return f'{m}:{s:02d}'
    duration_fmt.short_description = "Длит."

    def source_badge(self, obj):
        if obj.video_file:
            return format_html('<span style="color:green; font-weight:600;">📁 Файл</span>')
        if obj.link:
            return format_html('<span style="color:#007bff; font-weight:600;">🔗 Ссылка</span>')
        return format_html('<span style="color:#dc3545;">✗ Нет</span>')
    source_badge.short_description = "Источник"

    def open_video(self, obj):
        url = obj.get_video_url()
        if url:
            return format_html(
                '<a href="{}" target="_blank" style="background:#28a745; color:#fff; '
                'padding:4px 10px; border-radius:4px; text-decoration:none; font-size:12px;">'
                '▶ Смотреть</a>', url
            )
        return format_html('<span style="color:#aaa;">Нет видео</span>')
    open_video.short_description = "Просмотр"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_teacher_or_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_teacher_or_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(VideoType)
class VideoTypeAdmin(admin.ModelAdmin):
    """Типы видео (Лекция, Практика, Вебинар…).
    Преподаватели видят список только для ориентации;
    создание и изменение — исключительно администратор.
    """
    list_display  = ('name', 'videos_count')
    search_fields = ('name',)
    ordering      = ('name',)

    def videos_count(self, obj):
        return Video.objects.filter(type=obj).count()
    videos_count.short_description = "Видео"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)

    def get_readonly_fields(self, request, obj=None):
        if not is_admin(request.user):
            return ('name',)
        return ()


# ══════════════════════════════════════════════════════════════════════════════
# ░░░░░░░░░░░░░░░░░░  РАЗДЕЛ: СТАТИСТИКА  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# Все разделы — только чтение (add/change заблокированы).
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    """Результаты тестирования. Только просмотр для всех ролей."""
    list_display    = ('user', 'test', 'score_badge', 'correct_summary', 'completed_at')
    readonly_fields = ('user', 'test', 'score', 'started_at', 'completed_at')
    list_filter     = ('test', 'completed_at')
    search_fields   = ('user__email', 'test__title')
    ordering        = ('-completed_at',)
    inlines         = [UserAnswerInline]

    def score_badge(self, obj):
        if obj.score >= 80:
            color, label = '#28a745', 'Отлично'
        elif obj.score >= 50:
            color, label = '#fd7e14', 'Нормально'
        else:
            color, label = '#dc3545', 'Плохо'
        return format_html(
            '<b style="color:{};">{:.0f}%</b> '
            '<span style="color:#999; font-size:11px;">({})</span>',
            color, obj.score, label,
        )
    score_badge.short_description = "Результат"

    def correct_summary(self, obj):
        correct = UserAnswer.objects.filter(test_result=obj, is_correct=True).count()
        total   = UserAnswer.objects.filter(test_result=obj).count()
        return f"{correct} / {total}"
    correct_summary.short_description = "Верных"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    """Все ответы пользователей — аналитика ошибок. Только чтение."""
    list_display    = ('user_email', 'test_name', 'question_short', 'correct_badge', 'answered_at')
    list_filter     = ('is_correct', 'answered_at', 'test_result__test')
    search_fields   = ('test_result__user__email', 'question__text')
    ordering        = ('-answered_at',)
    readonly_fields = ('test_result', 'question', 'chosen_answer', 'is_correct', 'answered_at')

    def user_email(self, obj):
        return obj.test_result.user.email if obj.test_result.user else "Аноним"
    user_email.short_description = "Пользователь"

    def test_name(self, obj):
        return obj.test_result.test.title if obj.test_result.test else "—"
    test_name.short_description = "Тест"

    def question_short(self, obj):
        t = obj.question.text
        return (t[:55] + '…') if len(t) > 55 else t
    question_short.short_description = "Вопрос"

    def correct_badge(self, obj):
        if obj.is_correct:
            return format_html('<span style="color:green; font-size:16px;">✓</span>')
        return format_html('<span style="color:#dc3545; font-size:16px;">✗</span>')
    correct_badge.short_description = "Верно?"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    """Сессии тренажёра (создаются автоматически). Только чтение."""
    list_display    = ('user', 'lesson_info', 'status_badge', 'questions_count', 'created_at', 'completed_at')
    list_filter     = ('status', 'lesson__block__subject')
    readonly_fields = ('user', 'lesson', 'status', 'source_test_result', 'created_at', 'completed_at')
    search_fields   = ('user__email', 'lesson__title')
    ordering        = ('-created_at',)
    inlines         = [TrainingQuestionInline]

    def lesson_info(self, obj):
        if obj.lesson:
            return f"{obj.lesson.title} ({obj.lesson.block.subject.name})"
        return "Общий тренажёр"
    lesson_info.short_description = "Урок"

    def status_badge(self, obj):
        cfg = {
            'active':    ('#007bff', '● Активна'),
            'completed': ('#28a745', '✓ Завершена'),
            'abandoned': ('#6c757d', '✗ Прервана'),
        }
        color, label = cfg.get(obj.status, ('#666', obj.status))
        return format_html('<span style="color:{}; font-weight:600;">{}</span>', color, label)
    status_badge.short_description = "Статус"

    def questions_count(self, obj):
        return obj.training_questions.count()
    questions_count.short_description = "Вопросов"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(TrainingQuestion)
class TrainingQuestionAdmin(admin.ModelAdmin):
    """Вопросы внутри сессий тренажёра (автоматическое управление). Только чтение."""
    list_display    = ('session_short', 'question_short', 'status', 'correct_badge', 'answered_at')
    list_filter     = ('status', 'session__lesson__block__subject')
    readonly_fields = ('session', 'question', 'chosen_answer', 'is_correct', 'position', 'status', 'answered_at')
    search_fields   = ('question__text',)
    ordering        = ('session', 'position')

    def session_short(self, obj):
        return str(obj.session.id)[:8] + '…'
    session_short.short_description = "Сессия"

    def question_short(self, obj):
        t = obj.question.text
        return (t[:55] + '…') if len(t) > 55 else t
    question_short.short_description = "Вопрос"

    def correct_badge(self, obj):
        if obj.is_correct is None:
            return format_html('<span style="color:#aaa;">—</span>')
        if obj.is_correct:
            return format_html('<span style="color:green; font-size:16px;">✓</span>')
        return format_html('<span style="color:#dc3545; font-size:16px;">✗</span>')
    correct_badge.short_description = "Верно?"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


# ══════════════════════════════════════════════════════════════════════════════
# КАСТОМНЫЙ ДАШБОРД (передаём статистику в контекст главной страницы)
# ══════════════════════════════════════════════════════════════════════════════

def _custom_index(self, request, extra_context=None):
    extra_context = extra_context or {}
    try:
        from .models import Subject, Test, User, TestResult, Block, Lesson, Video

        extra_context['subjects_count'] = Subject.objects.count()
        extra_context['tests_count']    = Test.objects.count()
        extra_context['students_count'] = User.objects.filter(role='student').count()
        extra_context['results_count']  = TestResult.objects.count()
        extra_context['blocks_count']   = Block.objects.count()
        extra_context['lessons_count']  = Lesson.objects.count()
        extra_context['videos_count']   = Video.objects.count()

        extra_context['recent_results'] = (
            TestResult.objects
            .select_related('user', 'test')
            .order_by('-completed_at')[:8]
        )
        extra_context['subjects_tree'] = (
            Subject.objects
            .prefetch_related('blocks__lessons__video', 'blocks__final_test')
            .all()
        )
        extra_context['recent_students'] = (
            User.objects.filter(role='student').order_by('-id')[:6]
        )
    except Exception as e:
        if settings.DEBUG:
            raise
        logger.error("Ошибка при формировании дашборда: %s", e)

    return _orig_index(self, request, extra_context=extra_context)


_AdminSite.index = _custom_index