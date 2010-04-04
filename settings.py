# Django settings for cms project.
import os
settings_dir = os.path.dirname(__file__)

try:
    from settings_private import *
except:
    pass

TEMPLATE_DEBUG = DEBUG

TIME_ZONE = 'America/Los_Angeles'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1
USE_I18N = True

MEDIA_ROOT = os.path.join(settings_dir, 'media')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media/admin/'

CACHE_BACKEND =	'memcached://127.0.0.1:11211'
CACHE_MIDDLEWARE_SECONDS = 60 *	5
CACHE_MIDDLEWARE_KEY_PREFIX = 'palewire'
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(settings_dir, 'templates/'),
    os.path.join(settings_dir, 'rapture/templates/'),
)

STATIC_DOC_ROOT = os.path.join(settings_dir, 'rapture/archive/html')

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.flatpages',
    'django.contrib.comments',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    'coltrane',
    'tagging',
    'kennedy',
    'robots',
    'correx',
    'rapture',

)

