from django import forms
from django.forms import formset_factory
from .models import Subject, Block, Lesson, Video, Test

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']
        labels = {
            'name': 'Название предмета',
        }

class BlockForm(forms.ModelForm):
    class Meta:
        model = Block
        fields = ['title', 'description', 'final_test', 'position', 'is_published']
        labels = {
            'title': 'Название блока',
            'description': 'Описание',
            'final_test': 'Итоговый тест',
            'position': 'Позиция',
            'is_published': 'Опубликовано',
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'summary', 'duration', 'video', 'test', 'position', 'is_published']
        labels = {
            'title': 'Название урока',
            'summary': 'Краткое содержание',
            'duration': 'Длительность (сек)',
            'video': 'Видео',
            'test': 'Тест',
            'position': 'Позиция',
            'is_published': 'Опубликовано',
        }

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['name', 'description', 'video_file', 'link', 'type', 'duration']
        labels = {
            'name': 'Название видео',
            'description': 'Описание',
            'video_file': 'Файл видео',
            'link': 'Ссылка на видео',
            'type': 'Тип видео',
            'duration': 'Длительность (сек)',
        }

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'duration', 'is_published']
        labels = {
            'title': 'Название теста',
            'description': 'Описание теста',
            'duration': 'Длительность (сек)',
            'is_published': 'Опубликовано',
        }

# Formsets for creating multiple objects
BlockFormSet = formset_factory(BlockForm, extra=1)
LessonFormSet = formset_factory(LessonForm, extra=1)
