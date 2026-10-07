"""Настройки ИС Price (MVP подмодуля «Маркетинговый анализ с маршрутом согласования»).

Все параметры окружения читаются из переменных среды (см. README, раздел «Переменные окружения»).
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    value = os.environ.get(name)
    return int(value) if value not in (None, "") else default


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-secret-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.core",
    "apps.nsi",
    "apps.suppliers",
    "apps.pricing",
    "apps.marketing_analysis",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# PostgreSQL 17 в проде (DATABASE_URL=postgres://...); SQLite — только для локального запуска и тестов.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=env_int("DB_CONN_MAX_AGE", 60),
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "ru"
LANGUAGES = [("ru", "Русский"), ("kk", "Қазақша")]
TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Almaty")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Файловое хранилище (on-premise). Файлы КП и PDF-заключения отдаются только через API с проверкой прав,
# поэтому MEDIA_ROOT не публикуется через nginx.
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))
MEDIA_URL = "/media/"
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 30 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
}

# --- Celery / Redis ---
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", None)
# Без брокера (локальный запуск, тесты) задачи выполняются синхронно.
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", True)
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_TIMEZONE = TIME_ZONE

CACHES = {
    "default": (
        {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": os.environ["REDIS_CACHE_URL"]}
        if os.environ.get("REDIS_CACHE_URL")
        else {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    )
}

# --- Email ---
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = env_int("EMAIL_PORT", 25)
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "price@kmg.kz")
PORTAL_BASE_URL = os.environ.get("PORTAL_BASE_URL", "http://localhost:5173")

# --- Регуляторные параметры ---
# Ставка НДС РК, %. С 01.01.2026 по новому Налоговому кодексу РК — 16%. Проверить перед вводом в эксплуатацию.
VAT_RATE_PERCENT = env_int("VAT_RATE_PERCENT", 16)
BASE_CURRENCY = "KZT"

# --- Подмодуль «Маркетинговый анализ с маршрутом согласования» ---
# Фича-флаг: при False API подмодуля отвечает 404, пункт меню скрыт.
MA_ENABLED = env_bool("MA_ENABLED", True)
# TODO(PO): вопрос 1 — минимальное количество КП на позицию перед отправкой.
MA_MIN_KP_COUNT = env_int("MA_MIN_KP_COUNT", 1)
# TODO(PO): вопрос 2 — согласующие этапа 1 только из ДЗО анализа или любые.
MA_DZO_APPROVERS_SAME_DZO_ONLY = env_bool("MA_DZO_APPROVERS_SAME_DZO_ONLY", True)
# TODO(PO): вопрос 2 — режим этапа 1. Реализован только последовательный режим.
MA_DZO_STAGE_MODE = "sequential"
# TODO(PO): вопрос 3 — можно ли отправить без согласующих этапа 1 сразу в ДБ КМГ.
MA_ALLOW_SKIP_DZO_STAGE = env_bool("MA_ALLOW_SKIP_DZO_STAGE", False)
# TODO(PO): вопрос 4 — после доработки маршрут заново (True) или с вернувшего этапа (False).
MA_RESTART_ROUTE_FROM_BEGINNING = env_bool("MA_RESTART_ROUTE_FROM_BEGINNING", True)
# TODO(PO): вопрос 5 — этап ДБ КМГ: любой пользователь с ролью ("role") или назначенный конкретный.
MA_DB_STAGE_ASSIGNMENT = os.environ.get("MA_DB_STAGE_ASSIGNMENT", "role")
# TODO(PO): вопрос 6 — проверка отклонения от средней по КМГ с отправкой Ответственному КМГ. Пока только показ в аналитике.
MA_KMG_DEVIATION_CHECK_ENABLED = env_bool("MA_KMG_DEVIATION_CHECK_ENABLED", False)
MA_KMG_DEVIATION_THRESHOLD_PERCENT = env_int("MA_KMG_DEVIATION_THRESHOLD_PERCENT", 15)
# TODO(PO): вопрос 7 — префикс номера нового типа анализа (по умолчанию формат текущих заявок ID2026.EMG.0001).
MA_NUMBER_PREFIX = os.environ.get("MA_NUMBER_PREFIX", "ID")
# Метод расчёта маркетинговой цены: "average" (среднее арифметическое КП) или "min" (минимальная цена).
# TODO(PO): подтвердить методику — в MVP нет действующего сервиса расчёта, по умолчанию среднее арифметическое.
MA_PRICE_CALC_METHOD = os.environ.get("MA_PRICE_CALC_METHOD", "average")
# Согласующим этапа 1 не может быть автор анализа. TODO(PO): подтвердить правило.
MA_ALLOW_AUTHOR_AS_APPROVER = env_bool("MA_ALLOW_AUTHOR_AS_APPROVER", False)
MA_ALLOWED_OFFER_EXTENSIONS = ["pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png"]
MA_MAX_UPLOAD_MB = env_int("MA_MAX_UPLOAD_MB", 25)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
