from django.contrib import admin
from django.utils.html import format_html
from .models import (
    User, Group, GroupMember, Subject, Block,
    Lesson, Test, Question, Answer, Video, TestResult, VideoType, UserAnswer
)


# --- Вспомогательные классы (Inlines) ---

class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    # Делаем поля только для чтения, так как это история ответов
    readonly_fields = ('question', 'chosen_answer', 'is_correct', 'answered_at')
    extra = 0
    can_delete = False
    verbose_name = "Ответ пользователя"
    verbose_name_plural = "Детализация ответов"

    def has_add_permission(self, request, obj=None):
        return False  # Запрещаем добавлять ответы вручную


# --- AUTH & GROUPS ---

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'lastname', 'firstname', 'role')
    list_filter = ('role',)
    search_fields = ('email', 'lastname')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group')
    list_filter = ('group',)


# --- CONTENT & VIDEO ---

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'position')
    list_filter = ('subject',)
    list_editable = ('position',)


@admin.register(VideoType)
class VideoTypeAdmin(admin.ModelAdmin):  # Исправлено имя класса
    list_display = ('id', 'name')


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'block', 'position', 'duration', 'video_details')
    list_filter = ('block',)
    list_editable = ('position', 'duration',)

    def video_details(self, obj):
        if obj.video:
            v = obj.video
            v_type = v.type.name if hasattr(v.type, 'name') else v.type
            return format_html(
                '<span style="font-size: 11px; line-height: 1.2;">'
                '<b>Тип:</b> {}<br><b>Длительность:</b> {} сек.<br><b>URL:</b> {}</span>',
                v_type, v.duration, (v.link[:25] + '...') if v.link else '---'
            )
        return format_html('<span style="color: #999;">Видео не привязано</span>')

    video_details.short_description = "Параметры видео"


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'duration', 'link_preview', 'open_video')
    list_filter = ('type',)
    list_editable = ('type',)

    def link_preview(self, obj):
        return obj.link[:30] + "..." if obj.link else "---"

    def open_video(self, obj):
        if obj.link:
            return format_html(
                '<a class="button" href="{}" target="_blank" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 4px;">▶ Смотреть</a>',
                obj.link)
        return "Нет ссылки"


# --- TESTS & ANSWERS ---

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test')
    inlines = [AnswerInline]
    list_filter = ('test',)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_published')
    list_editable = ('is_published',)


# --- РЕЗУЛЬТАТЫ (ГЛАВНОЕ ИЗМЕНЕНИЕ) ---

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score_colored', 'correct_answers_count', 'completed_at')
    readonly_fields = ('user', 'test', 'score', 'started_at', 'completed_at')
    list_filter = ('test', 'user')

    # Добавляем Inline с ответами пользователя прямо в результат теста
    inlines = [UserAnswerInline]

    def score_colored(self, obj):
        color = "green" if obj.score >= 80 else "orange" if obj.score >= 50 else "red"
        return format_html('<b style="color: {};">{}%</b>', color, obj.score)

    score_colored.short_description = "Баллы"

    def correct_answers_count(self, obj):
        # Считаем количество записей UserAnswer с флагом is_correct=True для этого результата
        count = UserAnswer.objects.filter(test_result=obj, is_correct=True).count()
        total = UserAnswer.objects.filter(test_result=obj).count()
        return f"{count} из {total}"

    correct_answers_count.short_description = "Верных ответов"


# Отдельно регистрируем UserAnswer, если нужно смотреть их общим списком
@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'test_name', 'question', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'answered_at')

    def user_email(self, obj):
        return obj.test_result.user.email

    user_email.short_description = "Пользователь"

    def test_name(self, obj):
        return obj.test_result.test.title

    test_name.short_description = "Тест"