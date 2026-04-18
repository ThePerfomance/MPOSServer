# api/admin.py
from django.contrib import admin
from .models import User, Subject, Block, Lesson, Video, Test, Question, Answer

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'lastname', 'firstname', 'role', 'is_staff')
    search_fields = ('email', 'lastname')
    list_filter = ('role', 'is_staff')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'block', 'position', 'is_published')
    list_editable = ('position', 'is_published') # Позволяет менять прямо в списке
    search_fields = ('title',)

# Простая регистрация для остальных
admin.site.register(Subject)
admin.site.register(Block)
admin.site.register(Video)
admin.site.register(Test)
admin.site.register(Question)
admin.site.register(Answer)