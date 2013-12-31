# -*- coding: utf-8
from __future__ import absolute_import
import os
import decimal
import sys
# on change le context par defaut
decimal.getcontext().rouding = decimal.ROUND_HALF_UP
decimal.getcontext().precision = 3
# chemin du projet
PROJECT_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
BASE_DIR = PROJECT_PATH

DEFAULT_CHARSET = 'utf-8'
DEBUG = False
TEMPLATE_DEBUG = DEBUG
DJANGO_EXTENSION = True
# TEMPLATE_STRING_IF_INVALID="INVALID"

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
ID_CAT_COTISATION = 2
ID_TIERS_COTISATION = 1
# id des operations sur titre elle doit s'appeler 'Opération sur titre'
ID_CAT_OST = 3
# elle doit s'appeler 'Revenus de placement:Plus-values'
ID_CAT_PMV = 4
# moyen par defaut pour les ope de recette
MD_CREDIT = 1
# moyen par defaut pour les ope de depenses
MD_DEBIT = 2
REV_PLAC = 5
ID_CAT_VIR = 1
DIR_DROPBOX = "D:\Dropbox"
##################
ATOMIC_REQUESTS = True
WSGI_APPLICATION = "gsb.wsgi.application"
ADMINS = (
    # ('toto', 'your_email@domain.com'),
)

MANAGERS = ADMINS
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.join(PROJECT_PATH, 'grisbi.sqlite'),  # Or path to database file if using sqlite3.
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
LANGUAGE_CODE = 'fr-FR'
FIRST_DAY_OF_WEEK = 1
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
MEDIA_ROOT = "C:/django/gsb/upload"

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = 'media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PROJECT_PATH, '/static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

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
    from .secret_key import *  # @UnusedWildImport

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #    'django.template.loaders.eggs.Loader',
)

if DJANGO_TOOLBAR:
    MIDDLEWARE_CLASSES = ('debug_toolbar.middleware.DebugToolbarMiddleware',
                            'django.contrib.sessions.middleware.SessionMiddleware',
                            'django.middleware.common.CommonMiddleware',)
else:
    MIDDLEWARE_CLASSES = ('django.contrib.sessions.middleware.SessionMiddleware',
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
    'django.contrib.admindocs',
    'django_extensions',
    'south'
)
if DJANGO_TOOLBAR:
    DEBUG_TOOLBAR_CONFIG = {
        # If set to True (default), the debug toolbar will show an intermediate
        # page upon redirect so you can view any debug information prior to
        # redirecting. This page will provide a link to the redirect destination
        # you can follow when ready. If set to False, redirects will proceed as
        # normal.
        'INTERCEPT_REDIRECTS': False,

        # If not set or set to None, the debug_toolbar middleware will use its
        # built-in show_toolbar method for determining whether the toolbar should
        # show or not. The default checks are that DEBUG must be set to True and
        # the IP of the request must be in INTERNAL_IPS. You can provide your own
        # method for displaying the toolbar which contains your custom logic. This
        # method should return True or False.
        'SHOW_TOOLBAR_CALLBACK': None,

        # An array of custom signals that might be in your project, defined as the
        # python path to the signal.
        'EXTRA_SIGNALS': [],

        # If set to True (the default) then code in Django itself won't be shown in
        # SQL stacktraces.
        'HIDE_DJANGO_SQL': True,

        # If set to True (the default) then a template's context will be included
        # with it in the Template debug panel. Turning this off is useful when you
        # have large template contexts, or you have template contexts with lazy
        # datastructures that you don't want to be evaluated.
        'SHOW_TEMPLATE_CONTEXT': True,

        # If set, this will be the tag to which debug_toolbar will attach the debug
        # toolbar. Defaults to 'body'.
        'TAG': 'body',
    }
    DEBUG_TOOLBAR_PANELS = ('debug_toolbar.panels.version.VersionDebugPanel',
                            'debug_toolbar.panels.timer.TimerDebugPanel',
                            'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
                            'debug_toolbar.panels.headers.HeaderDebugPanel',
                            'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
                            'debug_toolbar.panels.template.TemplateDebugPanel',
                            'debug_toolbar.panels.sql.SQLDebugPanel',
                            'debug_toolbar.panels.signals.SignalDebugPanel',
                            'debug_toolbar.panels.logger.LoggingPanel',
                            'template_timings_panel.panels.TemplateTimings.TemplateTimings',
                            'inspector_panel.panels.inspector.InspectorPanel'
                           )
    INSTALLED_APPS += ('debug_toolbar',
                        'template_timings_panel',
                        'inspector_panel'
                        )
    #https://github.com/santiagobasulto/debug-inspector-panel
    #https://github.com/orf/django-debug-toolbar-template-timings
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
