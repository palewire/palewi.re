# Django settings for cms project.
import os
import dj_database_url
import django_heroku

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_DIR = os.path.join(BASE_DIR, "project")
ROOT_DIR = BASE_DIR

DEBUG = os.environ.get("DEBUG") != "false"
PRODUCTION = os.environ.get("PRODUCTION") == "true"
SECRET_KEY = os.environ.get("SECRET_KEY", "foobar")

MEDIA_URL = "http://palewire.s3.amazonaws.com/"
ADMIN_MEDIA_PREFIX = "http://palewire.s3.amazonaws.com/admin/"
STATIC_URL = "/static/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
STATIC_ROOT = os.path.join(BASE_DIR, ".staticfiles")
STATICFILES_DIRS = ()
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

TIME_ZONE = "America/Los_Angeles"
USE_TZ = False
LANGUAGE_CODE = "en-us"
SITE_ID = 1
USE_I18N = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "palewire",
        "USER": "postgres",
        "HOST": "localhost",
    }
}
DATABASES["default"].update(dj_database_url.config(conn_max_age=500, ssl_require=True))

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

MIDDLEWARE = (
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
)

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "toolbox.context_processors.current_site",
                "toolbox.context_processors.now",
            ],
            "debug": DEBUG,
        },
    },
]


INSTALLED_APPS = (
    "django.contrib.messages",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.admin",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    "django.contrib.staticfiles",
    # Blog
    "coltrane",
    "bona_fides",
    "django_comments",
    # Site extras and helpers
    "greeking",
    "adminsortable",
    'whitenoise.runserver_nostatic',
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": [
                "require_debug_false",
            ],
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "formatters": {
        "verbose": {
            "format": "%(levelname)s|%(asctime)s|%(module)s|%(process)d|%(thread)d|%(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s|%(message)s"},
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "handlers": ["null"],
            "propagate": False,
        },
        "coltrane": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "wxwtf": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

GITHUB_USER = "palewire"
TWITTER_USER = "palewire"
TWITTER_CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN_KEY = os.environ.get("TWITTER_ACCESS_TOKEN_KEY")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_RETWEET_TXT = "RT %s: "
TWITTER_REMOVE_LINKS = False

# Activate Django-Heroku.
django_heroku.settings(locals())
