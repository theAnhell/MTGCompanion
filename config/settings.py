import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-secret-key")
DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "players",
    "commanders",
    "games",
    "decks",
    "binder",
    "cards",
    "recommendations",
    "stats",
    "imports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True

# The source export's timestamps carry no timezone info (MythicTrack app
# writes local wall-clock time as a naive string) and the Node version stores
# them as-is with no conversion. Keeping the whole project naive avoids
# Django silently reinterpreting those timestamps as UTC.
USE_TZ = False

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# The React app runs on Vite's dev server, separate from this API.
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173", "http://127.0.0.1:5173"]
)

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": None,
    "EXCEPTION_HANDLER": "config.exceptions.exception_handler",
}

# Mirrors the Node import scripts' env-driven file paths (see MythicTrack/.env.example).
GAMES_EXPORT_PATH = env("GAMES_EXPORT_PATH", default=str(BASE_DIR / "data" / "AllGames.json"))
RETIRED_GLOBAL_PATH = env("RETIRED_GLOBAL_PATH", default=str(BASE_DIR / "data" / "retired_decks.json"))
RETIRED_DIR_PATH = env("RETIRED_DIR_PATH", default=str(BASE_DIR / "data" / "retired"))
PLAYER_MERGES_PATH = env("PLAYER_MERGES_PATH", default=str(BASE_DIR / "data" / "player-merges.json"))
MOXFIELD_DECKS_CONFIG_PATH = env(
    "MOXFIELD_DECKS_CONFIG_PATH", default=str(BASE_DIR / "data" / "moxfield-decks.json")
)

# EDHREC inclusion-rate cutoffs (%) for the recommendation engine: a
# collection card is worth suggesting as an add once this popular; a card
# already in the deck is worth suggesting as a cut once this rare.
RECOMMENDATION_ADD_THRESHOLD = env.float("RECOMMENDATION_ADD_THRESHOLD", default=60.0)
RECOMMENDATION_REMOVE_THRESHOLD = env.float("RECOMMENDATION_REMOVE_THRESHOLD", default=15.0)

# Target counts for the archetype/deckbuilding-requirements check (Card.roles).
DECK_TARGET_RAMP = env.int("DECK_TARGET_RAMP", default=10)
DECK_TARGET_DRAW = env.int("DECK_TARGET_DRAW", default=10)
DECK_TARGET_REMOVAL = env.int("DECK_TARGET_REMOVAL", default=10)
DECK_TARGET_LANDS = env.int("DECK_TARGET_LANDS", default=37)
