import os
from pathlib import Path
import dj_database_url

SITE_URL = "https://www.drop-delivery.ru"

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------- .env загрузка (без падений) ----------
try:
    from dotenv import load_dotenv, find_dotenv
    # 1) BASE_DIR/.env
    load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)
    # 2) поиск вверх по дереву, если запустили из другого cwd
    if not os.getenv("DJANGO_SECRET_KEY"):
        load_dotenv(find_dotenv(filename=".env", usecwd=True), override=True)
except Exception:
    pass

# ---------- База ----------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "drop-delivery.ru,www.drop-delivery.ru,.railway.app,127.0.0.1,localhost"
).split(",")

CSRF_TRUSTED_ORIGINS = os.getenv(
    "DJANGO_CSRF_TRUSTED",
    "https://drop-delivery.ru,https://www.drop-delivery.ru,https://*.railway.app"
).split(",")

# За обратным прокси (Railway/Cloudflare)
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("DJANGO_SSL_REDIRECT", "True") == "True"

# ---------- Apps ----------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # сторонние
    "anymail",          # <-- HTTPS email через провайдеров (SendGrid, Mailgun, Resend и т.п.)
    "widget_tweaks",

    # проект
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

APPEND_SLASH = True

ROOT_URLCONF = "dandd.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context.site_globals",
                "core.context.stations_nav",
            ],
        },
    },
]

WSGI_APPLICATION = "dandd.wsgi.application"

# ---------- Database ----------
DB_SSL_REQUIRE = os.getenv("DB_SSL_REQUIRE", "True") == "True"
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL", "postgres://dd_user:dd_password@localhost:5432/dd_db"),
        conn_max_age=600,
        ssl_require=DB_SSL_REQUIRE,
    )
}

# ---------- Auth ----------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------- I18N/Time ----------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# ---------- Static / WhiteNoise ----------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------- Telegram ----------
def _split_ids(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]

TELEGRAM_BOT_NAME = os.getenv("TELEGRAM_BOT_NAME", "")
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")  # опционально
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
TELEGRAM_SHARED_TOKEN = os.getenv("TELEGRAM_SHARED_TOKEN", "")

ADMIN_TG_CHAT_ID = os.getenv("ADMIN_TG_CHAT_ID", "").strip()
TELEGRAM_CHAT_IDS = _split_ids(os.getenv("TELEGRAM_CHAT_IDS", ""))

if ADMIN_TG_CHAT_ID and ADMIN_TG_CHAT_ID not in TELEGRAM_CHAT_IDS:
    TELEGRAM_CHAT_IDS.insert(0, ADMIN_TG_CHAT_ID)

# ---------- Email: API first (Anymail/SendGrid), SMTP остаётся для локалки ----------
# По умолчанию используем HTTPS-бэкенд (никаких SMTP-блокировок в PaaS)
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "anymail.backends.sendgrid.EmailBackend"
)
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    os.getenv("EMAIL_HOST_USER", "") or "no-reply@drop-delivery.ru"
)

# Anymail (SendGrid) настройки
ANYMAIL = {
    "SENDGRID_API_KEY": os.getenv("SENDGRID_API_KEY", ""),
}
ANYMAIL_REQUESTS_TIMEOUT = int(os.getenv("ANYMAIL_TIMEOUT", "8"))

# --- Старые SMTP-поля (используются, если EMAIL_BACKEND переключишь на SMTP) ---
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.yandex.ru")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))     # 465(SSL) или 587(TLS)
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False") == "True"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "True") == "True"
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "8"))

# ---------- Кэш (нужен для send_once) ----------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "dd_cache",   # имя таблицы
        "TIMEOUT": 300,
    }
}
# Если таблицы нет, создай один раз:
# python manage.py createcachetable dd_cache

# ---------- Логи ----------
LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}
