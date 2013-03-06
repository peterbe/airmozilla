# This is your project's main settings file that can be committed to your
# repo. If you need to override a setting locally, use settings_local.py

from funfactory.settings_base import *

# Name of the top-level module where you put all your apps.
# If you did not install Playdoh with the funfactory installer script
# you may need to edit this value. See the docs about installing from a
# clone.
PROJECT_MODULE = 'airmozilla'


# Defines the views served for root URLs.
ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

INSTALLED_APPS = list(INSTALLED_APPS) + [
    # Application base, containing global templates.
    '%s.base' % PROJECT_MODULE,
    '%s.main' % PROJECT_MODULE,
    '%s.auth' % PROJECT_MODULE,
    '%s.manage' % PROJECT_MODULE,
    '%s.suggest' % PROJECT_MODULE,

    'bootstrapform',
    'sorl.thumbnail',
    'south',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.flatpages',
]

# our session storage is all memcache so using it instead of FallbackStorage
# which uses CookieStorage by default so sessions are better
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Because Jinja2 is the default template loader, add any non-Jinja templated
# apps here:
JINGO_EXCLUDE_APPS = [
    'admin',
    'registration',
    'bootstrapform',
]

# BrowserID configuration
AUTHENTICATION_BACKENDS = [
    'django_browserid.auth.BrowserIDBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PROFILE_MODULE = 'main.UserProfile'

# Domains allowed for log in
ALLOWED_BID = ['mozilla.com', 'mozillafoundation.org']

SITE_URL = 'http://127.0.0.1:8000'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = 'main:home'
LOGIN_REDIRECT_URL_FAILURE = 'main:login_failure'

TEMPLATE_CONTEXT_PROCESSORS += (
    'django_browserid.context_processors.browserid_form',
    'airmozilla.manage.context_processors.badges',
    'airmozilla.main.context_processors.sidebar',
    'airmozilla.main.context_processors.analytics',
)

# Always generate a CSRF token for anonymous users.
ANON_ALWAYS = True

# Tells the extract script what files to look for L10n in and what function
# handles the extraction. The Tower library expects this.
DOMAIN_METHODS['messages'] = [
    ('%s/**.py' % PROJECT_MODULE,
        'tower.management.commands.extract.extract_tower_python'),
    ('%s/**/templates/**.html' % PROJECT_MODULE,
        'tower.management.commands.extract.extract_tower_template'),
    ('templates/**.html',
        'tower.management.commands.extract.extract_tower_template'),
],

# # Use this if you have localizable HTML files:
# DOMAIN_METHODS['lhtml'] = [
#    ('**/templates/**.lhtml',
#        'tower.management.commands.extract.extract_tower_template'),
# ]

# # Use this if you have localizable JS files:
# DOMAIN_METHODS['javascript'] = [
#    # Make sure that this won't pull in strings from external libraries you
#    # may use.
#    ('media/js/**.js', 'javascript'),
# ]

LOGGING = dict(loggers=dict(playdoh={'level': logging.DEBUG}))

# Remove localization middleware
MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
MIDDLEWARE_CLASSES.remove('funfactory.middleware.LocaleURLMiddleware')
MIDDLEWARE_CLASSES.insert(0, 'airmozilla.locale_middleware.' +
                             'LocaleURLMiddleware')
MIDDLEWARE_CLASSES.append(
    'airmozilla.manage.middleware.CacheBustingMiddleware'
)
MIDDLEWARE_CLASSES.append(
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware'
)
MIDDLEWARE_CLASSES = tuple(MIDDLEWARE_CLASSES)

# Enable timezone support for Django TZ-aware datetime objects
# Times stored in the db as UTC; forms/templates as Pacific time
USE_TZ = True
TIME_ZONE = 'US/Pacific'

# Configuration for live/archiving events treatment
# How much time, in minutes, an event shows as "live" before its start time.
LIVE_MARGIN = 10

# Default amount of time, in minutes, an event spends in the "archiving" state.
ARCHIVING_MARGIN = 60

# How many events in the past (and future) should the calendar system
# return.  E.g. if CALENDAR_SIZE=30, up to 60 events (half from the past
# and half from the future) will be output.
CALENDAR_SIZE = 30

# How many events should appear in the syndication feeds
FEED_SIZE = 20

# Use PNG for thumbnailing
THUMBNAIL_FORMAT = 'PNG'

# Number of upcoming events to display in the sidebar
UPCOMING_SIDEBAR_COUNT = 3

# Use memcached for session storage
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# Always use secure cookies
COOKIES_SECURE = True

# Defaults for Mozillians
MOZILLIANS_API_BASE = 'https://mozillians.org'

# API base URL
VIDLY_API_URL = 'http://m.vid.ly/api/'

# Name of the default Channel
DEFAULT_CHANNEL_SLUG = 'main'
DEFAULT_CHANNEL_NAME = 'Main'
