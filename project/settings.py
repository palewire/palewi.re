# Django settings for palewi.re
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_DIR = os.path.join(BASE_DIR, "project")
ROOT_DIR = BASE_DIR

PRODUCTION = os.environ.get("PRODUCTION") == "true"
DEBUG = not PRODUCTION and os.environ.get("DEBUG", "true").lower() != "false"

_default_secret = "" if PRODUCTION else "dev-only-insecure-secret-key-not-for-production"
SECRET_KEY = os.environ.get("SECRET_KEY", _default_secret)
if PRODUCTION and not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set in production.")

#
# Static files
#

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "collected_static")
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if PRODUCTION
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

TIME_ZONE = "America/Los_Angeles"
USE_TZ = True
LANGUAGE_CODE = "en-us"
USE_I18N = True

ALLOWED_HOSTS = (
    # Include palewire.com and www.palewire.com so that DomainRedirectMiddleware
    # can handle those requests before returning 400 DisallowedHost.
    ["palewi.re", "www.palewi.re", ".palewi.re", ".herokuapp.com", "palewire.com", "www.palewire.com"]
    if PRODUCTION
    else os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
)

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "toolbox.middleware.domains.DomainRedirectMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.static",
                "toolbox.context_processors.repository",
            ],
            "debug": DEBUG,
        },
    },
]


INSTALLED_APPS = [
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    # Blog
    "coltrane",
    # Site extras and helpers
    "whitenoise.runserver_nostatic",
]

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

#
# Production security
#

if PRODUCTION:
    # Cloudflare may connect to the Heroku origin over HTTP after terminating
    # TLS. Allow that deployment to disable Django's redirect and avoid a loop.
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "true").lower() == "true"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
