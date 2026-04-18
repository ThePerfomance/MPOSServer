from django.contrib import admin
from django.utils.html import format_html # Импорт для генерации HTML-кнопок
from .models import (
    User, Group, GroupMember, Subject, Block,
    Lesson, Test, Question, Answer, Video, TestResult
)

# --- AUTH ---
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'lastname', 'firstname', 'role')
    list_filter = ('role',)
    search_fields = ('email', 'lastname')

# --- GROUPS ---
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group')
    list_filter = ('group',)

# --- CONTENT ---
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'position')
    list_filter = ('subject',)
    list_editable = ('position',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'block', 'position')
    list_filter = ('block',)
    list_editable = ('position',)

# --- ТРЕНАЖЕРЫ (ВИДЕО) ---
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    # Добавлена колонка для быстрого перехода к плееру
    list_display = ('link', 'type', 'duration', 'open_video')
    list_filter = ('type',)

    def open_video(self, obj):
        if obj.link:
            return format_html('<a class="button" href="{}" target="_blank" style="background-color: #417690; color: white; padding: 5px 10px; border-radius: 4px;">Смотреть</a>', obj.link)
        return "Нет ссылки"
    open_video.short_description = "Тренажер"

# --- ТЕСТЫ ---
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test')
    inlines = [AnswerInline]
    list_filter = ('test',) # Удобно фильтровать вопросы по тестам

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'description', 'duration', 'is_published')

# --- РЕЗУЛЬТАТЫ ---
@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    # Добавлена кнопка для просмотра всех вопросов теста данного пользователя
    list_display = ('user', 'test', 'score', 'completed_at', 'review_answers')
    readonly_fields = ('started_at', 'completed_at')
    list_filter = ('test', 'user')

    def review_answers(self, obj):
        # Эта кнопка ведет в раздел Вопросов, отфильтрованных по текущему тесту
        url = f"/admin/api/question/?test__id__exact={obj.test.id}"
        return format_html('<a class="button" href="{}" style="padding: 5px 10px; border: 1px solid #ccc; border-radius: 4px;">Проверить ответы</a>', url)
    review_answers.short_description = "Анализ ответов"