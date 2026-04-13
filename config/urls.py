# config/urls.py (или MPOSServer/urls.py) - Главный файл URL-адресов проекта
from django.contrib import admin
from django.urls import path, include
from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), # <-- Вход
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # <-- Обновление токена
]