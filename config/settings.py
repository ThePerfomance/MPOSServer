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
    'api.apps.ApiConfig',
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'api' / 'templates'],
        'APP_DIRS': True,
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
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME":  timedelta(days=7),
}

# ══════════════════════════════════════════════════════════════════════════════
# JAZZMIN — основные настройки
# ══════════════════════════════════════════════════════════════════════════════

JAZZMIN_SETTINGS = {
    # ── Брендинг ─────────────────────────────────────────────────────────────
    "site_title":    "Edu Platform",
    "site_header":   "Учебная платформа",
    "site_brand":    "EduSystem",
    "site_logo":     None,                 # путь к logo, если есть: "img/logo.png"
    "welcome_sign":  "Добро пожаловать в панель управления",
    "copyright":     "Nikita Smolnikov",

    # ── Поиск ────────────────────────────────────────────────────────────────
    "search_model": ["api.User"],

    "hide_apps":   ["auth"],
    "hide_models": [],

    "topmenu_links": [
        {
            "name": "🏠 Главная",
            "url":  "admin:index",
        },
        {
            "name": "📚 Обучение",
            "children": [
                {"name": "📖 Предметы",   "url": "admin:api_subject_changelist"},
                {"name": "📦 Блоки",       "url": "admin:api_block_changelist"},
                {"name": "🎬 Уроки",       "url": "admin:api_lesson_changelist"},
                {"name": "📝 Тесты",       "url": "admin:api_test_changelist"},
                {"name": "❓ Вопросы",     "url": "admin:api_question_changelist"},
                {"name": "✅ Ответы",      "url": "admin:api_answer_changelist"},
            ],
        },
        {
            "name": "👥 Пользователи",
            "children": [
                {"name": "👤 Пользователи",    "url": "admin:api_user_changelist"},
                {"name": "🏫 Группы",          "url": "admin:api_group_changelist"},
                {"name": "➕ Участники групп", "url": "admin:api_groupmember_changelist"},
            ],
        },
        {
            "name": "🎥 Видео",
            "children": [
                {"name": "🎞 Видеоматериалы", "url": "admin:api_video_changelist"},
                {"name": "🏷 Типы видео",     "url": "admin:api_videotype_changelist"},
            ],
        },
        {
            "name": "📊 Статистика",
            "children": [
                {"name": "🏆 Результаты тестов",     "url": "admin:api_testresult_changelist"},
                {"name": "✏️ Ответы пользователей",  "url": "admin:api_useranswer_changelist"},
                {"name": "🏋 Сессии тренажёра",      "url": "admin:api_trainingsession_changelist"},
                {"name": "🔀 Вопросы тренажёра",     "url": "admin:api_trainingquestion_changelist"},
            ],
        },
    ],

    # ── Порядок моделей в боковой панели ─────────────────────────────────────
    # Порядок строго соответствует логической иерархии разделов
    "order_with_respect_to": [
        # Обучение
        "api.subject",
        "api.block",
        "api.lesson",
        "api.test",
        "api.question",
        "api.answer",
        # Пользователи
        "api.user",
        "api.group",
        "api.groupmember",
        # Видео
        "api.video",
        "api.videotype",
        # Статистика
        "api.testresult",
        "api.useranswer",
        "api.trainingsession",
        "api.trainingquestion",
    ],

    # ── Иконки (Font Awesome 5) ───────────────────────────────────────────────
    "icons": {
        # Приложение
        "api": "fas fa-graduation-cap",
        # Обучение
        "api.subject":         "fas fa-book",
        "api.block":           "fas fa-cube",
        "api.lesson":          "fas fa-film",
        "api.test":            "fas fa-clipboard-check",
        "api.question":        "fas fa-question-circle",
        "api.answer":          "fas fa-check-square",
        # Пользователи
        "api.user":            "fas fa-user",
        "api.group":           "fas fa-users",
        "api.groupmember":     "fas fa-user-plus",
        # Видео
        "api.video":           "fas fa-video",
        "api.videotype":       "fas fa-tags",
        # Статистика
        "api.testresult":      "fas fa-chart-bar",
        "api.useranswer":      "fas fa-pen",
        "api.trainingsession": "fas fa-dumbbell",
        "api.trainingquestion":"fas fa-tasks",
    },
    "default_icon_parents":  "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    # ── Sidebar / навигация ───────────────────────────────────────────────────
    "show_sidebar":          True,
    "navigation_expanded":   True,
    "related_modal_active":  True,     # открывать FK-связи в модальном окне

    # ── Пользовательское меню (иконка профиля в правом верхнем углу) ─────────
    "usermenu_links": [
        {"name": "Главная страница сайта", "url": "/", "new_window": True, "icon": "fas fa-home"},
    ],

    # ── Быстрый поиск ────────────────────────────────────────────────────────
    "show_ui_builder": False,   # отключаем кнопку «UI Builder» в продакшене
                                # (включите True, чтобы поиграть с темой)
}

# ══════════════════════════════════════════════════════════════════════════════
# JAZZMIN — визуальные настройки (UI Tweaks)
# ══════════════════════════════════════════════════════════════════════════════
JAZZMIN_UI_TWEAKS = {
    # Тема Bootstrap
    "theme":           "flatly",
    "dark_mode_theme": "darkly",   # тема для тёмного режима

    # Размер текста
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text":   False,
    "brand_small_text":  False,

    # Верхняя навигационная полоса
    "navbar":           "navbar-white navbar-light",   # светлый стиль
    "no_navbar_border": False,
    "navbar_fixed":     True,   # фиксируем navbar при прокрутке

    # Боковая панель
    "sidebar":          "sidebar-dark-primary",
    "sidebar_fixed":    True,
    "sidebar_nav_small_text":    False,
    "sidebar_disable_expand":    False,
    "sidebar_nav_child_indent":  True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style":  False,
    "sidebar_nav_flat_style":    False,

    # Стили кнопок
    "button_classes": {
        "primary":   "btn-primary",
        "secondary": "btn-outline-secondary",
        "info":      "btn-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },

    # Стили actions
    "actions_sticky_top": True,    # панель действий фиксируется сверху
}

# ══════════════════════════════════════════════════════════════════════════════
# Прочие настройки Django
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ     = True
TIME_ZONE  = 'UTC'
AUTH_USER_MODEL = 'api.User'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ['email', 'firstname', 'lastname', 'patronymic'],
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ru-ru'

# Статика и медиа
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = []

MEDIA_URL  = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')