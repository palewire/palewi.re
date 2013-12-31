# Django settings for cms project.
import os
settings_dir = os.path.dirname(__file__)
SETTINGS_DIR = settings_dir
ROOT_DIR = os.path.join(
    os.path.abspath(
        os.path.join(SETTINGS_DIR, os.path.pardir),
    ),
)

MEDIA_URL = 'http://palewire.s3.amazonaws.com/'
ADMIN_MEDIA_PREFIX = 'http://palewire.s3.amazonaws.com/admin/'
STATIC_URL = '/static/'

try:
    from settings_dev import *
except ImportError:
    from settings_prod import *
TEMPLATE_DEBUG = DEBUG

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

TEMPLATE_DIRS = (
    os.path.join(ROOT_DIR, 'templates/'),
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

STATICFILES_DIRS = (
    os.path.join(ROOT_DIR, 'templates/static/'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)


TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.csrf",
    "toolbox.context_processors.sites.current_site",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.comments',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
     # Blog
    'coltrane',
    'bona_fides',
     # Site extras and helpers
    'correx',
    'tagging',
    'django_extensions',
    'greeking',
    'shortener',
    'south',
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
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
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


if DEBUG_TOOLBAR:
    INTERNAL_IPS = ('127.0.0.1',)
    # Debugging toolbar middleware
    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )
    # JavaScript panels for the deveopment debugging toolbar
    DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.version.VersionDebugPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel',
        'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
        'debug_toolbar.panels.headers.HeaderDebugPanel',
        'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
        'debug_toolbar.panels.template.TemplateDebugPanel',
        'debug_toolbar.panels.sql.SQLDebugPanel',
        'debug_toolbar.panels.signals.SignalDebugPanel',
        'debug_toolbar.panels.logger.LoggingPanel',
    )
    # Debug toolbar app
    INSTALLED_APPS += ('debug_toolbar',)
    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
        'HIDE_DJANGO_SQL': False,
    }

