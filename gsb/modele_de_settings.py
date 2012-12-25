# -*- coding: utf-8
import os
import decimal
import sys
# on change le context par defaut
decimal.getcontext().rouding = decimal.ROUND_HALF_UP
decimal.getcontext().precision = 3
PROJECT_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))

DEFAULT_CHARSET = 'utf-8'
DEBUG = False
TEMPLATE_DEBUG = DEBUG
DJANGO_EXTENSION = True
# TEMPLATE_STRING_IF_INVALID="INVALID"

DEBUG_PROPAGATE_EXCEPTIONS = False

ADMINS = (
# ('toto', 'your_email@domain.com'),
)
#####################################
# config gsb
TITRE = "20040701_django.gsb"
DEVISE_GENERALE = 'EUR'
ID_CPT_M = 1  # cpt principal utlise si l'on ne rentre pas de compte
AFFICHE_CLOT = False  # affiche les comptes clos
UTILISE_EXERCICES = False
UTILISE_IB = True
UTILISE_PC = False

# taux de cotisations sociales
# attention c'est un taux special estime
__TAUX_VERSEMENT_legal = 0.08 * 0.97
TAUX_VERSEMENT = decimal.Decimal(str(1 / (1 - __TAUX_VERSEMENT_legal) * __TAUX_VERSEMENT_legal))
# id et cat des operation speciales
ID_CAT_COTISATION = 23
ID_TIERS_COTISATION = 727
ID_CAT_OST = 64
ID_CAT_PMV = 4
MD_CREDIT = 6
MD_DEBIT = 7
##################

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(PROJECT_PATH, 'grisbi.db'),  # Or path to database file if using sqlite3.
        'USER': 'root',  # Not used with sqlite3.
        'PASSWORD': '',  # Not used with sqlite3.
        'HOST': '',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
    }
}
if 'testserver' in sys.argv:
    DATABASES['default']['TEST_NAME'] = os.path.join(PROJECT_PATH, 'test_db.db')
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
LANGUAGE_CODE = 'fr-fr'
THOUSAND_SEPARATOR = " "
DECIMAL_SEPARATOR = ','
FIRST_DAY_OF_WEEK = 1
MONTH_DAY_FORMAT = 'l j F'
NUMBER_GROUPING = 3
USE_THOUSAND_SEPARATOR = True

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'  # plus utilise car deprecated

# Additional locations of static files
STATICFILES_DIRS = (
# Put strings here, like "/home/html/static" or "C:/www/django/static".
# Always use forward slashes, even on Windows.
# Don't forget to use absolute paths, not relative paths.
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
    fichier = open(nomfich, 'w')
    fichier.write("# -*- coding: utf-8 -*-")
    fichier.write("SECRET_KEY=%s" % secret)
    from secret_key import *  # @UnusedWildImport

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
    )

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware'
    )

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'templates'),
    )

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gsb',
    # gestion admin
    'django.contrib.admin',
    'django.contrib.admindocs'
    )
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.static',
    )
if DJANGO_EXTENSION:
    INSTALLED_APPS += ('django_extensions',)

# noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
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
