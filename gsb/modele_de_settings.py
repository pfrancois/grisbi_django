# -*- coding: utf-8

import os
import decimal
import sys

# chemin du projet
PROJECT_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
BASE_DIR = PROJECT_PATH

DEFAULT_CHARSET = 'utf-8'
DEBUG = False
TEMPLATE_DEBUG = DEBUG
DJANGO_EXTENSION = True
DJANGO_TOOLBAR = False
# TEMPLATE_STRING_IF_INVALID = "INVALID"
TEMPLATE_STRING_IF_INVALID = ""
#
# config gsb
# titre affiche dans export gsb
TITRE = "20040701_django.gsb"
# devise utilise
DEVISE_GENERALE = 'EUR'
# compte utilise comme contrepartie par defaut en virement
ID_CPT_M = 1
# affiche les comptes clos
AFFICHE_CLOT = False
# utilise les exercices
UTILISE_EXERCICES = False
UTILISE_IB = True
UTILISE_PC = False

# taux de cotisations sociales
# attention c'est un taux special estime
__TAUX_VERSEMENT_legal = 0.08 * 0.97
TAUX_VERSEMENT = decimal.Decimal(str(1 / (1 - __TAUX_VERSEMENT_legal) * __TAUX_VERSEMENT_legal))
# id et cat des operation speciales
ID_TIERS_COTISATION = 1
ID_CAT_COTISATION = 2
# id des operations sur titre elle doit s'appeler 'Opération sur titre'
ID_CAT_OST = 3
ID_CAT_VIR = 1
# elle doit s'appeler 'Revenus de placement:Plus-values'
ID_CAT_PMV = 4
# moyen par defaut pour les ope de recette
MD_CREDIT = 1
# moyen par defaut pour les ope de depenses
MD_DEBIT = 2
REV_PLAC = 5

DIR_DROPBOX = r"D:\Dropbox"
# code du pc pour pocket money
CODE_DEVICE_POCKET_MONEY = 'tobedefined'

ATOMIC_REQUESTS = True
WSGI_APPLICATION = "gsb.wsgi.application"

INSTALLED_APPS = (
    'adminactions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gsb',
    # gestion admin
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django_extensions',
    'colorful',
    'rest_framework',
    'django_ajax'
)
REST_FRAMEWORK = {  # Use Django's standard `django.contrib.auth` permissions,
                    # or allow read-only access for unauthenticated users.
                    #'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly' ]
                    'PAGINATE_BY': 10,
                    'DEFAULT_MODEL_SERIALIZER_CLASS': 'drf_toolbox.serializers.ModelSerializer',
}

try:
    TESTING = 'test' == sys.argv[1]
except IndexError:
    TESTING = False
COVERAGE_APPS = ('gsb',)
COVERAGE_HTML_OPEN_IN_BROWSER = False
COVERAGE_HTML_BROWSER_OPEN_TYPE = 'existing'
COVERAGE_REPORT_TYPE = 'html'
COVERAGE_CODE_EXCLUDES = ['raise AssertionError',
                            'raise NotImplementedError',
                            'pragma: no cover',
                            r'if self\.debug',
                            'if not settings.TESTING:']
COVERAGE_EXCLUDE_MODULES = (
    'gsb.tests',
    'gsb.perso',
    'gsb.sql',
    'gsb.migrations',
    'gsb.secret_key',
    'gsb.settings',
    'gsb.wsgi')
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
INTERNAL_IPS = ("127.0.0.1", "localhost")

ADMINS = (  # ('Your Name', 'your_email@domain.com'),
)
SERIALIZATION_MODULES = {'yaml': 'gsb.io.yamlserial', }
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                         # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
                         #'NAME': os.path.join(PROJECT_PATH, 'test.sqlite'), # Or path to database file if using sqlite3.
                         'NAME': os.path.join(PROJECT_PATH, 'grisbi.sqlite'),
                         # Or path to database file if using sqlite3.
                         'USER': 'root',  # Not used with sqlite3.
                         'PASSWORD': '',  # Not used with sqlite3.
                         'HOST': '',  # Set to empty string for localhost. Not used with sqlite3.
                         'PORT': '',  # Set to empty string for default. Not used with sqlite3.}
                         }
             }
if 'test' in sys.argv or 'testserver':
    TEST = True
LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/"
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'
USE_TZ = True
# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True
LANGUAGE_CODE = 'fr-FR'
FIRST_DAY_OF_WEEK = 1
USE_THOUSAND_SEPARATOR = True
DATE_INPUT_FORMATS = (
    '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%y',  # '2006-10-25', '10/25/2006', '10/25/06'
    '%d %b %Y', '%d %b, %Y',  # '25 Oct 2006', '25 Oct, 2006'
    '%b %d %Y', '%b %d, %Y',  # 'Oct 25 2006', 'Oct 25, 2006'
    '%d %B %Y', '%d %B, %Y',  # '25 October 2006', '25 October, 2006'
    '%B %d %Y', '%B %d, %Y',  # 'October 25 2006', 'October 25, 2006'

)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, "upload")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = 'media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_PATH, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
try:
    from .secret_key import *
except ImportError:
    SETTINGS_DIR = os.path.abspath(os.path.dirname(__file__))
    nomfich = os.path.join(PROJECT_PATH, 'secret_key.py')
    from random import choice

    secret = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
    fichier = open(nomfich, 'w', encoding="utf-8")
    fichier.write("# -*- coding: utf-8 -*-")
    fichier.write("SECRET_KEY=%s" % secret)
    from .secret_key import *  # @UnusedWildImport

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    #('django.template.loaders.cached.Loader', (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #)),
)

if DJANGO_TOOLBAR:
    MIDDLEWARE_CLASSES = (
        'debug_toolbar.middleware.DebugToolbarMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',)
else:
    MIDDLEWARE_CLASSES = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',)

MIDDLEWARE_CLASSES += (
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'templates'),
)

if DJANGO_TOOLBAR:
    DEBUG_TOOLBAR_CONFIG = {'JQUERY_URL': '/static/js/jquery.js'}
    DEBUG_TOOLBAR_PANELS = ('debug_toolbar.panels.versions.VersionsPanel',
                            'debug_toolbar.panels.timer.TimerPanel',
                            'debug_toolbar.panels.settings.SettingsPanel',
                            'debug_toolbar.panels.headers.HeadersPanel',
                            'debug_toolbar.panels.request.RequestPanel',
                            'debug_toolbar.panels.templates.TemplatesPanel',
                            'debug_toolbar.panels.sql.SQLPanel',
                            'debug_toolbar.panels.signals.SignalsPanel',
                            'debug_toolbar.panels.logging.LoggingPanel',
                            )

    INSTALLED_APPS += ('debug_toolbar',)
    # https://github.com/santiagobasulto/debug-inspector-panel
    # https://github.com/orf/django-debug-toolbar-template-timings
    IGNORED_TEMPLATES = ["debug_toolbar/*"]
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.static',
)

# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
if False and not DJANGO_TOOLBAR:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '[%(levelname)s] %(asctime)s - %(name)s - %(pathname)s:%(lineno)d in %(funcName)s,  MSG:%(message)s'
            },
        },
        'handlers': {
            'null': {
                'level': 'DEBUG',
                'class': 'django.utils.log.NullHandler',
            },
            'console-simple': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose'
            },
            'log-file': {
                'level': 'WARNING',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'verbose',
                # consider: 'filename': '/var/log/<myapp>/app.log',
                # will need perms at location below:
                'filename': os.path.join(PROJECT_PATH, 'log', 'gsb_log.log'),
                'when': 'D',
                'backupCount': '30',  # approx 1 month worth
            },
        },
        'loggers': {
            'django': {
                'level': 'WARNING',
                'handlers': ['console-simple', 'log-file'],
                'propagate': True,
            },
            'django.request': {
                'level': 'DEBUG',
                'handlers': ['console-simple', 'log-file'],
                'propagate': False,
            },
            'django.db.backends': {
                'level': 'WARNING',
                'handlers': ['console-simple', 'log-file'],
                'propagate': False,
            },
            'gsb': {
                'level': 'INFO',
                'handlers': ['console-simple', 'log-file'],
                'propagate': True,
            }
        }
    }
