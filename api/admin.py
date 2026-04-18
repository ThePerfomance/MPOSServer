from django.contrib import admin
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
    list_display = ('id', 'name') # В модели Group только name
    search_fields = ('name',)

@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'group')
    list_filter = ('group',)

# --- CONTENT ---
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',) # В модели Subject именно title

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

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    # В твоей модели Video только url и type. Связи с Lesson НЕТ.
    list_display = ('link', 'type', 'duration')
    list_filter = ('type',)

# --- TESTS ---
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test')
    inlines = [AnswerInline]

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    # В модели Test только связь с lesson (OneToOneField)
    list_display = ('id', 'title', 'description', 'duration', 'is_published')

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score', 'completed_at')
    readonly_fields = ('started_at', 'completed_at')