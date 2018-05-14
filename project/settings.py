# Django settings for cms project.
import os
from django.core.exceptions import SuspiciousOperation
settings_dir = os.path.dirname(__file__)
SETTINGS_DIR = settings_dir
ROOT_DIR = os.path.join(
    os.path.abspath(
        os.path.join(SETTINGS_DIR, os.path.pardir),
    ),
)
BASE_DIR = ROOT_DIR

MEDIA_URL = 'http://palewire.s3.amazonaws.com/'
ADMIN_MEDIA_PREFIX = 'http://palewire.s3.amazonaws.com/admin/'
STATIC_URL = '/static/'

try:
    from settings_dev import *
except ImportError:
    from settings_prod import *

TIME_ZONE = 'America/Los_Angeles'
USE_TZ = False
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True

MEDIA_ROOT = os.path.join(ROOT_DIR, 'media')
STATIC_ROOT = os.path.join(ROOT_DIR, 'static')

CACHE_BACKEND =	'memcached://127.0.0.1:11211'
CACHE_MIDDLEWARE_SECONDS = 60 * 5
CACHE_MIDDLEWARE_KEY_PREFIX = ''
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

HAYSTACK_SITECONF = 'coltrane.search_indexes'
HAYSTACK_SEARCH_ENGINE = 'whoosh'
HAYSTACK_WHOOSH_PATH = '/apps/palewire.com/whoosh/'

MUNIN_ROOT = '/var/cache/munin/www/'

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'toolbox.middleware.domains.MultipleProxyMiddleware',
    'django.middleware.common.CommonMiddleware',
    'toolbox.middleware.domains.DomainRedirectMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'project.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.csrf",
                "toolbox.context_processors.sites.current_site",
                "toolbox.context_processors.sites.now",
            ],
        },
    },
]

STATICFILES_DIRS = (
    os.path.join(ROOT_DIR, 'templates/static/'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'autoarchive',
     # Blog
    'coltrane',
    'bona_fides',
    'django_comments',
     # Site extras and helpers
    'correx',
    'greeking',
    'adminsortable',
    # NICAR-related apps
    'nicar.polls',
    'nicar.flu_map',
    # Goofy one-off apps
    'wxwtf.questionheds',
    'wxwtf.random_oscars_ballot',
    'wxwtf.flushots',
    'wxwtf.kennedy',
)

# Shortener settings
SITE_NAME = 'palewi.re'
SITE_BASE_URL = 'http://%s/!/' % SITE_NAME


def skip_suspicious_operations(record):
  if record.exc_info:
    exc_value = record.exc_info[1]
    if isinstance(exc_value, SuspiciousOperation):
      return False
  return True


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'skip_suspicious_operations': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': skip_suspicious_operations,
         },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false', 'skip_suspicious_operations'],
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(settings_dir, 'django.log'),
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s|%(asctime)s|%(module)s|%(process)d|%(thread)d|%(message)s',
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s|%(message)s'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'coltrane': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'wxwtf': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}


# Django debug toolbar configuration
if DEBUG_TOOLBAR:
    # Debugging toolbar middleware
    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
    # JavaScript panels for the deveopment debugging toolbar
    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.profiling.ProfilingPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    )
    # Debug toolbar app
    INSTALLED_APPS += ('debug_toolbar',)
    CONFIG_DEFAULTS = {
        'INTERCEPT_REDIRECTS': False,
    }
