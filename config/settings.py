import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-key")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "corsheaders",
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True
ROOT_URLCONF = "config.urls"

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
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = False