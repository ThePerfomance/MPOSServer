# config/settings.py

import os
import re
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-key")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'jazzmin',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True
ROOT_URLCONF = "config.urls"

TEMPLATES = [ # <-- Добавлено для admin
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], # Укажите здесь пути к вашим кастомным шаблонам, если есть
        'APP_DIRS': True, # Искать шаблоны в директориях приложений
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database — parse DATABASE_URL
DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://eduuser:edupassword@db:5432/edudb")

_m = re.match(
    r"postgres://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<name>.+)",
    DATABASE_URL,
)
_db = _m.groupdict() if _m else {}

DATABASES = {
    "default": {
        "ENGINE":   "django.db.backends.postgresql",
        "NAME":     _db.get("name",     "edudb"),
        "USER":     _db.get("user",     "eduuser"),
        "PASSWORD": _db.get("password", "edupassword"),
        "HOST":     _db.get("host",     "db"),
        "PORT":     _db.get("port",     "5432"),
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60), # Время жизни access токена
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),   # Время жизни refresh токена
    # ... другие настройки ...
}

JAZZMIN_SETTINGS = {
    "site_title": "Edu Platform Admin",
    "site_header": "Edu Platform",
    "site_brand": "Система обучения",
    "welcome_sign": "Добро пожаловать в админку проекта",
    "copyright": "Nikita Smolnikov",
    "search_model": ["api.User"], # Быстрый поиск по пользователям
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "api.user": "fas fa-user",
        "api.lesson": "fas fa-book-open",
        "api.video": "fas fa-video",
    },
}

# Включаем UI Customizer (панель настроек справа, чтобы поиграться с цветами)
JAZZMIN_UI_TWEAKS = {
    # Тема всей админки (выбери одну из: flatly, darkly, slate, solar, yeti)
    "theme": "flatly",

    # Цветовая схема для кнопок и активных элементов
    "dark_mode_theme": "darkly",

    # Настройка навигации
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,

    # Цвет верхней панели (акцент)
    "navbar": "navbar-dark",
    "no_navbar_border": True,

    # Стиль кнопок (сделает их более современными и плоскими)
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = 'UTC'
AUTH_USER_MODEL = 'api.User'

# Настройки статических файлов (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

STATICFILES_DIRS = []

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')