# admin.py
from django.contrib import admin
from django.contrib.auth.models import Group as AuthGroup
from django.utils.html import format_html
from django.contrib.admin import AdminSite as _AdminSite
import logging
from django.conf import settings
from .models import (
    User, Group, GroupMember, TeacherGroup, GroupSubject, Subject, Block,
    Lesson, Test, Question, Answer, Video, TestResult, VideoType, UserAnswer,
    TrainingSession, TrainingQuestion
)

# ──────────────────────────────────────────────────────────────────────────────
# Убираем стандартную модель Groups из Django Auth, чтобы не путать с нашей.
# ──────────────────────────────────────────────────────────────────────────────
try:
    admin.site.unregister(AuthGroup)
except admin.sites.NotRegistered:
    pass

admin.site.site_header = "Учебная платформа — Администрирование"
admin.site.site_title = "Edu Platform"
admin.site.index_title = "Панель управления"

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ПРОВЕРКИ ПРАВ
# ══════════════════════════════════════════════════════════════════════════════

def is_admin(user):
    """Проверка: является ли пользователь администратором."""
    return hasattr(user, 'role') and user.role == 'admin'


def is_teacher_or_admin(user):
    """Проверка: является ли пользователь преподавателем или администратором."""
    return hasattr(user, 'role') and user.role in ('teacher', 'admin')


# ══════════════════════════════════════════════════════════════════════════════
# INLINE-КЛАССЫ (Вложенные формы)
# ══════════════════════════════════════════════════════════════════════════════

class AnswerInline(admin.TabularInline):
    """Варианты ответов внутри вопроса."""
    model = Answer
    extra = 4
    verbose_name = "Вариант ответа"
    verbose_name_plural = "Варианты ответов"
    fields = ('text', 'is_correct')


class UserAnswerInline(admin.TabularInline):
    """Детализация ответов внутри результата теста (только чтение)."""
    model = UserAnswer
    readonly_fields = ('question', 'chosen_answer', 'is_correct', 'points_earned', 'answered_at')
    extra = 0
    can_delete = False
    verbose_name = "Ответ"
    verbose_name_plural = "Детализация ответов"

    def has_add_permission(self, request, obj=None): return False

    def has_change_permission(self, request, obj=None): return False


class TrainingQuestionInline(admin.TabularInline):
    """Вопросы внутри сессии тренажёра (только чтение)."""
    model = TrainingQuestion
    readonly_fields = ('question', 'status', 'is_correct', 'chosen_answer', 'position')
    extra = 0
    can_delete = False
    verbose_name = "Вопрос"
    verbose_name_plural = "Вопросы в сессии"

    def has_add_permission(self, request, obj=None): return False

    def has_change_permission(self, request, obj=None): return False


class GroupMemberInline(admin.TabularInline):
    """Участники прямо внутри карточки группы."""
    model = GroupMember
    extra = 1
    autocomplete_fields = ('user',)
    verbose_name = "Участник"
    verbose_name_plural = "Состав группы"

class TeacherGroupInline(admin.TabularInline):
    """Преподаватели, прикрепленные к группе."""
    model = TeacherGroup
    extra = 1
    autocomplete_fields = ('teacher',)
    verbose_name = "Преподаватель"
    verbose_name_plural = "Преподаватели группы"


class GroupSubjectInline(admin.TabularInline):
    """Предметы, прикрепленные к группе."""
    model = GroupSubject
    extra = 1
    autocomplete_fields = ('subject',)
    verbose_name = "Предмет"
    verbose_name_plural = "Предметы группы"

# ══════════════════════════════════════════════════════════════════════════════
# Группы и преподаватели
# ══════════════════════════════════════════════════════════════════════════════
@admin.register(TeacherGroup)
class TeacherGroupAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'group')
    list_filter = ('group',)
    search_fields = ('teacher__email', 'teacher__lastname', 'group__name')
    autocomplete_fields = ('teacher', 'group')

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):              return is_admin(request.user)

    def has_change_permission(self, request, obj=None): return is_admin(request.user)

    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(GroupSubject)
class GroupSubjectAdmin(admin.ModelAdmin):
    list_display = ('group', 'subject')
    list_filter = ('group', 'subject')
    search_fields = ('group__name', 'subject__name')
    autocomplete_fields = ('group', 'subject')

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):              return is_admin(request.user)

    def has_change_permission(self, request, obj=None): return is_admin(request.user)

    def has_delete_permission(self, request, obj=None): return is_admin(request.user)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_admin(request.user): return qs
        # ИСПРАВЛЕНИЕ: фильтруем через связанный предмет (subject__creator)
        return qs.filter(subject__creator=request.user)
# ══════════════════════════════════════════════════════════════════════════════
# ░░░░░░░░░░░░░░░░░  РАЗДЕЛ: ОБУЧЕНИЕ  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Учебные предметы (Математика, Физика…)."""
    search_fields = ('name', 'creator__email', 'creator__lastname')
    list_filter = ('creator',)
    ordering = ('name',)

    def blocks_count(self, obj): return obj.blocks.count()
    blocks_count.short_description = "Кол-во блоков"

    def lessons_count(self, obj): return sum(b.lessons.count() for b in obj.blocks.all())
    lessons_count.short_description = "Кол-во уроков"

    def get_list_display(self, request):
        if is_admin(request.user):
            return ('name', 'creator', 'blocks_count', 'lessons_count')
        return ('name', 'blocks_count', 'lessons_count')

    def get_readonly_fields(self, request, obj=None):
        # Обычные преподаватели не могут менять создателя
        if not is_admin(request.user):
            return ('creator',)
        return ()

    def save_model(self, request, obj, form, change):
        # При создании предмета автоматически назначаем текущего пользователя создателем, если поле пустое
        if getattr(obj, 'creator', None) is None:
            obj.creator = request.user
        super().save_model(request, obj, form, change)

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_teacher_or_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_teacher_or_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    """Тематические блоки внутри предмета."""
    list_filter = ('subject', 'is_published')
    search_fields = ('title', 'subject__name')
    ordering = ('subject', 'position')

    def lessons_count(self, obj):
        return obj.lessons.count()

    lessons_count.short_description = "Уроков"

    def get_list_display(self, request):
        # Преподаватель видит упрощенный список без технических полей
        if is_admin(request.user):
            return ('title', 'subject', 'position', 'lessons_count', 'is_published')
        return ('title', 'subject', 'lessons_count')

    def get_list_editable(self, request):
        return ('position', 'is_published') if is_admin(request.user) else ()

    def get_fieldsets(self, request, obj=None):
        # Преподавателю показываем только суть, скрываем настройки публикации
        if is_admin(request.user):
            return (
                ('Основная информация', {'fields': ('title', 'subject', 'description')}),
                ('Настройки', {'fields': ('position', 'is_published')}),
                ('Итоговый тест', {'fields': ('final_test',)}),
            )
        return (
            ('Учебный материал', {'fields': ('title', 'subject', 'description', 'final_test')}),
        )

    def has_view_permission(self, request, obj=None):
        return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):
        return is_teacher_or_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return is_teacher_or_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_admin(request.user)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_admin(request.user): return qs
        return qs.filter(subject__creator=request.user)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Уроки: видеоматериал + тест + краткое содержание."""
    list_filter = ('block', 'block__subject', 'is_published')
    search_fields = ('title', 'summary', 'block__title')
    ordering = ('block', 'position')

    def video_info(self, obj):
        if not obj.video:
            return format_html('<span style="color:#aaa; font-style:italic;">Нет видео</span>')
        v = obj.video
        vtype = v.type.name if hasattr(v.type, 'name') else str(v.type)
        return format_html('<b>Тип:</b> {}<br><b>Длит.:</b> {} сек.', vtype, v.duration)

    video_info.short_description = "Видео"

    def get_list_display(self, request):
        # Преподаватель видит упрощенный список
        if is_admin(request.user):
            return ('title', 'block', 'position', 'duration', 'video_info', 'is_published')
        return ('title', 'block', 'video_info')

    def get_list_editable(self, request):
        return ('position', 'duration', 'is_published') if is_admin(request.user) else ()

    def get_fieldsets(self, request, obj=None):
        # Преподавателю даем простую форму для создания урока
        if is_admin(request.user):
            return (
                ('Основная информация', {'fields': ('title', 'block', 'summary')}),
                ('Медиа-контент', {'fields': ('video',)}),
                ('Тестирование', {'fields': ('test',)}),
                ('Настройки отображения', {'fields': ('position', 'duration', 'is_published')}),
            )
        return (
            ('Содержание урока', {'fields': ('title', 'block', 'summary', 'video', 'test')}),
        )

    def has_view_permission(self, request, obj=None):
        return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):
        return is_teacher_or_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return is_teacher_or_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_admin(request.user)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_admin(request.user): return qs
        return qs.filter(block__subject__creator=request.user)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    """Тесты."""
    list_filter = ('is_published',)
    search_fields = ('title', 'description')
    ordering = ('-id',)

    def questions_count(self, obj):
        return obj.questions.count()

    questions_count.short_description = "Вопросов"

    def duration_fmt(self, obj):
        if not obj.duration: return '∞ Без лимита'
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

    used_in.short_description = "Где прикреплен"

    def get_list_display(self, request):
        if is_admin(request.user):
            return ('title', 'duration_fmt', 'questions_count', 'is_published', 'used_in')
        return ('title', 'duration_fmt', 'questions_count', 'used_in')

    def get_list_editable(self, request):
        return ('is_published',) if is_admin(request.user) else ()

    def get_fieldsets(self, request, obj=None):
        if is_admin(request.user):
            return (
                ('Основная информация', {'fields': ('title', 'description')}),
                ('Настройки', {'fields': ('duration', 'is_published')}),
            )
        return (
            ('Создание теста', {'fields': ('title', 'description', 'duration')}),
        )

    def has_view_permission(self, request, obj=None):
        return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):
        return is_teacher_or_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return is_teacher_or_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_admin(request.user)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_admin(request.user): return qs
        return qs.filter(creator=request.user)

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'creator', None) is None: obj.creator = request.user
        super().save_model(request, obj, form, change)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Вопросы тестов."""
    list_display = ('text_preview', 'test', 'points', 'answers_count')
    list_filter = ('test',)
    search_fields = ('text',)
    inlines = [AnswerInline]
    ordering = ('test', 'id')

    def text_preview(self, obj):
        return (obj.text[:75] + '…') if len(obj.text) > 75 else obj.text

    text_preview.short_description = "Текст вопроса"

    def answers_count(self, obj):
        total = obj.answers.count()
        correct = obj.answers.filter(is_correct=True).count()
        color = 'green' if correct == 1 else ('orange' if correct == 0 else '#dc3545')
        return format_html('<span style="color:{};">{} вар. ({} верных)</span>', color, total, correct)

    answers_count.short_description = "Ответы"

    def get_fieldsets(self, request, obj=None):
        return (
            ('Вопрос', {'fields': ('text', 'test', 'points')}),
            ('Подсказки студенту (необязательно)', {
                'fields': ('recommendation_link', 'recommendation_video_link'),
                'classes': ('collapse',)
            }),
        )

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):              return is_teacher_or_admin(request.user)

    def has_change_permission(self, request, obj=None): return is_teacher_or_admin(request.user)

    def has_delete_permission(self, request, obj=None): return is_admin(request.user)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_admin(request.user): return qs
        return qs.filter(test__creator=request.user)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Варианты ответов."""
    list_display = ('text_preview', 'question_preview', 'is_correct')
    list_filter = ('is_correct', 'question__test')
    search_fields = ('text', 'question__text')

    def text_preview(self, obj): return (obj.text[:65] + '…') if len(obj.text) > 65 else obj.text

    text_preview.short_description = "Ответ"

    def question_preview(self, obj): return (obj.question.text[:55] + '…') if len(
        obj.question.text) > 55 else obj.question.text

    question_preview.short_description = "Вопрос"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):              return is_admin(request.user)

    def has_change_permission(self, request, obj=None): return is_admin(request.user)

    def has_delete_permission(self, request, obj=None): return is_admin(request.user)

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields] if not is_admin(request.user) else ()


# ══════════════════════════════════════════════════════════════════════════════
# ░░░░░░░░░░░░░░░░  РАЗДЕЛ: ПОЛЬЗОВАТЕЛИ  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Пользователи платформы."""
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'lastname', 'firstname')
    ordering = ('lastname', 'firstname')

    def full_name(self, obj):
        return f"{obj.lastname} {obj.firstname}".strip() or obj.email

    full_name.short_description = "Студент/Сотрудник"

    def role_badge(self, obj):
        cfg = {'admin': ('#dc3545', 'Админ'), 'teacher': ('#28a745', 'Преподаватель'),
               'student': ('#007bff', 'Студент')}
        color, label = cfg.get(obj.role, ('#666', obj.role))
        return format_html('<span style="color:{}; font-weight:600;">{}</span>', color, label)

    role_badge.short_description = "Роль"

    def get_list_display(self, request):
        if is_admin(request.user):
            return ('email', 'full_name', 'role_badge', 'is_active', 'is_staff')
        return ('email', 'full_name', 'role_badge')

    def get_fieldsets(self, request, obj=None):
        if is_admin(request.user):
            return (
                ('Личная информация', {'fields': ('firstname', 'lastname', 'patronymic', 'email')}),
                ('Настройки', {'fields': ('role', 'is_active', 'is_staff')}),
            )
        return (('Данные студента', {'fields': ('firstname', 'lastname', 'email', 'role')}),)

    def has_view_permission(self, request, obj=None):
        return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):
        return is_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return is_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_admin(request.user)

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields] if not is_admin(request.user) else ()


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'members_count', 'teachers_count', 'subjects_count')
    search_fields = ('name',)
    # Добавляем инлайны для управления всем прямо из карточки группы
    inlines = [TeacherGroupInline, GroupSubjectInline, GroupMemberInline]

    def members_count(self, obj): return obj.members.count()
    members_count.short_description = "Студентов"

    def teachers_count(self, obj): return obj.group_teachers.count()
    teachers_count.short_description = "Преподавателей"

    def subjects_count(self, obj): return obj.group_subjects.count()
    subjects_count.short_description = "Предметов"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)
    def has_add_permission(self, request):              return is_admin(request.user)
    def has_change_permission(self, request, obj=None): return is_admin(request.user)
    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group')
    list_filter = ('group',)
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
    list_filter = ('type',)
    search_fields = ('name', 'description')
    ordering = ('-id',)

    def duration_fmt(self, obj):
        if not obj.duration: return '—'
        m, s = divmod(obj.duration, 60)
        return f'{m}:{s:02d}'

    duration_fmt.short_description = "Длит."

    def source_badge(self, obj):
        if obj.video_file: return format_html('<span style="color:green;">📁 Файл</span>')
        if obj.link:       return format_html('<span style="color:#007bff;">🔗 Ссылка</span>')
        return format_html('<span style="color:#dc3545;">✗ Нет</span>')

    source_badge.short_description = "Источник"

    def get_list_display(self, request):
        return ('name', 'type', 'duration_fmt', 'source_badge')

    def get_fieldsets(self, request, obj=None):
        return (
            ('Информация о видео', {'fields': ('name', 'description', 'type', 'duration')}),
            ('Загрузка', {
                'fields': ('video_file', 'link'),
                'description': 'Прикрепите файл с компьютера ИЛИ вставьте ссылку на YouTube/Rutube',
            }),
        )

    def has_view_permission(self, request, obj=None):
        return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):
        return is_teacher_or_admin(request.user)

    def has_change_permission(self, request, obj=None):
        return is_teacher_or_admin(request.user)

    def has_delete_permission(self, request, obj=None):
        return is_admin(request.user)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_admin(request.user): return qs
        return qs.filter(creator=request.user)

    def save_model(self, request, obj, form, change):
        if getattr(obj, 'creator', None) is None: obj.creator = request.user
        super().save_model(request, obj, form, change)


@admin.register(VideoType)
class VideoTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):              return is_admin(request.user)

    def has_change_permission(self, request, obj=None): return is_admin(request.user)

    def has_delete_permission(self, request, obj=None): return is_admin(request.user)

    def get_readonly_fields(self, request, obj=None):
        return ('name',) if not is_admin(request.user) else ()


# ══════════════════════════════════════════════════════════════════════════════
# ░░░░░░░░░░░░░░░░░░  РАЗДЕЛ: СТАТИСТИКА  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
# ══════════════════════════════════════════════════════════════════════════════

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score_badge', 'points_summary', 'completed_at')
    readonly_fields = ('user', 'test', 'earned_points', 'total_points', 'started_at', 'completed_at')
    list_filter = ('test', 'completed_at')
    search_fields = ('user__email', 'test__title')
    ordering = ('-completed_at',)
    inlines = [UserAnswerInline]

    def score_badge(self, obj):
        if not obj.total_points:
            percentage = 0
        else:
            percentage = (obj.earned_points / obj.total_points) * 100

        if percentage >= 80:
            color, label = '#28a745', 'Отлично'
        elif percentage >= 50:
            color, label = '#fd7e14', 'Нормально'
        else:
            color, label = '#dc3545', 'Плохо'

        score_val = f"{percentage:.0f}"

        return format_html(
            '<b style="color:{};">{}%</b> '
            '<span style="color:#999; font-size:11px;">({})</span>',
            color, score_val, label,
        )

    score_badge.short_description = "Оценка"

    def points_summary(self, obj):
        return f"{obj.earned_points} из {obj.total_points}"

    points_summary.short_description = "Баллы"

    def has_view_permission(self, request, obj=None):
        return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return is_admin(request.user)


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'test_name', 'question_short', 'correct_badge', 'points_earned', 'answered_at')
    list_filter = ('is_correct', 'answered_at', 'test_result__test')
    search_fields = ('test_result__user__email', 'question__text')
    readonly_fields = ('test_result', 'question', 'chosen_answer', 'is_correct', 'points_earned', 'answered_at')

    def user_email(self, obj): return obj.test_result.user.email if obj.test_result.user else "Аноним"

    user_email.short_description = "Студент"

    def test_name(self, obj): return obj.test_result.test.title if obj.test_result.test else "—"

    test_name.short_description = "Тест"

    def question_short(self, obj): return (obj.question.text[:55] + '…') if len(
        obj.question.text) > 55 else obj.question.text

    question_short.short_description = "Вопрос"

    def correct_badge(self, obj):
        return format_html('<span style="color:green;">✓</span>') if obj.is_correct else format_html(
            '<span style="color:#dc3545;">✗</span>')

    correct_badge.short_description = "Верно?"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):              return False

    def has_change_permission(self, request, obj=None): return False

    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson_info', 'status_badge', 'created_at')
    list_filter = ('status', 'lesson__block__subject')
    readonly_fields = ('user', 'lesson', 'status', 'source_test_result', 'created_at', 'completed_at')
    inlines = [TrainingQuestionInline]

    def lesson_info(self, obj):
        return f"{obj.lesson.title}" if obj.lesson else "Общий тренажёр"

    lesson_info.short_description = "Урок"

    def status_badge(self, obj):
        cfg = {'active': ('#007bff', 'Активна'), 'completed': ('#28a745', 'Завершена'),
               'abandoned': ('#6c757d', 'Прервана')}
        color, label = cfg.get(obj.status, ('#666', obj.status))
        return format_html('<span style="color:{};">{}</span>', color, label)

    status_badge.short_description = "Статус"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):              return False

    def has_change_permission(self, request, obj=None): return False

    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


@admin.register(TrainingQuestion)
class TrainingQuestionAdmin(admin.ModelAdmin):
    list_display = ('session_short', 'question_short', 'correct_badge')
    list_filter = ('status',)
    readonly_fields = ('session', 'question', 'chosen_answer', 'is_correct', 'position', 'status', 'answered_at')

    def session_short(self, obj): return str(obj.session.id)[:8] + '…'

    session_short.short_description = "Сессия"

    def question_short(self, obj): return (obj.question.text[:55] + '…') if len(
        obj.question.text) > 55 else obj.question.text

    question_short.short_description = "Вопрос"

    def correct_badge(self, obj):
        if obj.is_correct is None: return "—"
        return format_html('<span style="color:green;">✓</span>') if obj.is_correct else format_html(
            '<span style="color:#dc3545;">✗</span>')

    correct_badge.short_description = "Верно?"

    def has_view_permission(self, request, obj=None):   return is_teacher_or_admin(request.user)

    def has_add_permission(self, request):              return False

    def has_change_permission(self, request, obj=None): return False

    def has_delete_permission(self, request, obj=None): return is_admin(request.user)


# ══════════════════════════════════════════════════════════════════════════════
# КАСТОМНЫЙ ДАШБОРД (ЕДИНЫЙ ДЛЯ АДМИНОВ И ПРЕПОДАВАТЕЛЕЙ)
# ══════════════════════════════════════════════════════════════════════════════

_orig_index = _AdminSite.index


def _custom_index(self, request, extra_context=None):
    extra_context = extra_context or {}
    try:
        from django.db.models import Q
        from .models import Subject, Test, User, TestResult, Block, Lesson, Video, Group

        user = request.user
        is_adm = getattr(user, 'role', '') == 'admin'

        if is_adm:
            # Администратор видит вообще всю статистику
            subjects_qs = Subject.objects.all()
            tests_qs = Test.objects.all()
            students_qs = User.objects.filter(role='student')
            results_qs = TestResult.objects.all()
            blocks_qs = Block.objects.all()
            lessons_qs = Lesson.objects.all()
            videos_qs = Video.objects.all()
        else:
            # Преподаватель видит только свои данные
            teacher_groups = Group.objects.filter(group_teachers__teacher=user)
            students_qs = User.objects.filter(role='student', memberships__group__in=teacher_groups).distinct()
            subjects_qs = Subject.objects.filter(
                Q(subject_groups__group__in=teacher_groups) | Q(creator=user)).distinct()
            blocks_qs = Block.objects.filter(subject__in=subjects_qs)
            lessons_qs = Lesson.objects.filter(block__subject__in=subjects_qs)
            tests_qs = Test.objects.filter(
                Q(lesson_for__block__subject__in=subjects_qs) | Q(final_block_of__subject__in=subjects_qs) | Q(
                    creator=user)).distinct()
            results_qs = TestResult.objects.filter(user__in=students_qs, test__in=tests_qs)
            videos_qs = Video.objects.filter(Q(creator=user) | Q(lessons__block__subject__in=subjects_qs)).distinct()

        # Заполняем счетчики
        extra_context.update({
            'subjects_count': subjects_qs.count(),
            'tests_count': tests_qs.count(),
            'students_count': students_qs.count(),
            'results_count': results_qs.count(),
            'blocks_count': blocks_qs.count(),
            'lessons_count': lessons_qs.count(),
            'videos_count': videos_qs.count(),
        })

        # Последние результаты (с расчетом процента "на лету")
        recent_results_qs = results_qs.select_related('user', 'test').order_by('-completed_at')[:8]
        recent_results = []
        for r in recent_results_qs:
            r.score = int((r.earned_points / r.total_points) * 100) if r.total_points else 0
            recent_results.append(r)

        extra_context['recent_results'] = recent_results
        extra_context['subjects_tree'] = subjects_qs.prefetch_related('blocks__lessons__video', 'blocks__final_test')
        extra_context['recent_students'] = students_qs.order_by('-id')[:6]

    except Exception as e:
        if settings.DEBUG:
            raise
        logger.error("Ошибка при формировании дашборда: %s", e)

    return _orig_index(self, request, extra_context=extra_context)


_AdminSite.index = _custom_index