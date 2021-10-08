"""
Django settings for giveaway_config project.

Generated by 'django-admin startproject' using Django 3.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path

import environ
from django.contrib.messages import constants as messages
from django.urls import reverse_lazy

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

environ.Env.read_env(str(BASE_DIR / ".env"))

SECRET_KEY = "django-insecure-1kf!1b$^k3$cbg!pm(s*^omit&i_%jcctzb@dx-5g8p!oz#y!g"

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "debug_toolbar",
    "huey.contrib.djhuey",
    "crispy_forms",
    "crispy_bootstrap5",
    "accounts",
    "giveaways",
    "payments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    # "payments.middleware.PaystackMiddleware",
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.Argon2PasswordHasher",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = ["accounts.backends.EmailBackend"]

LOGIN_URL = reverse_lazy("accounts:login")

LOGIN_REDIRECT_URL = reverse_lazy("core:index")

LOGOUT_REDIRECT_URL = reverse_lazy("core:index")

ROOT_URLCONF = "giveaway_config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "giveaways.context_processors.enums",
            ],
        },
    },
]

WSGI_APPLICATION = "giveaway_config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"

CRISPY_TEMPLATE_PACK = "bootstrap5"

MESSAGE_TAGS = {
    messages.DEBUG: "alert alert-primary",
    messages.INFO: "alert alert-info",
    messages.SUCCESS: "alert alert-success",
    messages.ERROR: "alert alert-danger",
    messages.WARNING: "alert alert-warning",
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

EMAIL_HOST = "localhost"

EMAIL_PORT = 25

DEFAULT_FROM_EMAIL = "noreply@giveaway.app"

REDIS_URL = "redis://localhost:6379/4"

HUEY = {
    "name": "giveaway",
    "huey_class": "huey.PriorityRedisExpireHuey",
    "immediate": False,
    "utc": True,
    "consumer": {
        "workers": 2,
        "worker_type": "thread",
        "initial_delay": 0.1,
        "backoff": 1.15,
        "max_delay": 10.0,
        "scheduler_interval": 1,
        "periodic": True,
        "check_worker_health": True,
    },
}

PAYSTACK_SECRET_KEY = env("PAYSTACK_TEST_SECRET")

PAYSTACK_PUBLIC_KEY = env("PAYSTACK_TEST_PUBLIC")

PAYSTACK_URL = "https://api.paystack.co"

PAYSTACK_CALLBACK_URL = "http://localhost:8000/payments/paystack/callback"
