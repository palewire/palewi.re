# Django settings for palewi.re
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_DIR = os.path.join(BASE_DIR, "project")
ROOT_DIR = BASE_DIR

DEBUG = os.environ.get("DEBUG", "true").lower() != "false"
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-key-not-for-production")
STATIC_MANIFEST = os.environ.get("STATIC_MANIFEST") == "true"

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
            "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
            if STATIC_MANIFEST
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

TIME_ZONE = "America/Los_Angeles"
USE_TZ = True
LANGUAGE_CODE = "en-us"
USE_I18N = True

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,palewi.re").split(",")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
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
    "bakery",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    # Blog
    "coltrane",
]

BUILD_DIR = os.path.join(BASE_DIR, "dist")
BAKERY_BUILD_HOST = "palewi.re"
BAKERY_VIEWS = [
    "coltrane.bakery_views.BioBuildView",
    "coltrane.bakery_views.ClipListBuildView",
    "coltrane.bakery_views.AppListBuildView",
    "coltrane.bakery_views.CodeListBuildView",
    "coltrane.bakery_views.GuideListBuildView",
    "coltrane.bakery_views.DocsLandingBuildView",
    "coltrane.bakery_views.TalkListBuildView",
    "coltrane.bakery_views.PostListBuildView",
    "coltrane.bakery_views.BotListBuildView",
    "coltrane.bakery_views.PostDetailBuildView",
    "coltrane.bakery_views.LatestPostsBuildFeed",
    "coltrane.bakery_views.LatestPostsJsonBuildFeed",
    "coltrane.bakery_views.RobotsBuildView",
    "coltrane.bakery_views.SecurityTxtBuildView",
    "coltrane.bakery_views.LLMsTxtBuildView",
    "coltrane.bakery_views.Static404BuildView",
    "coltrane.bakery_views.Static500BuildView",
    "coltrane.bakery_views.SitemapIndexBuildView",
    "coltrane.bakery_views.StaticSitemapBuildView",
    "coltrane.bakery_views.PostsSitemapBuildView",
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
