# config/urls.py (или MPOSServer/urls.py) - Главный файл URL-адресов проекта
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Подключаем api.urls под префиксом 'api/'
    path('api/', include('api.urls')), # <-- Правильный способ
    # path('', include('api.urls')), # <-- Было так (неправильно)
]