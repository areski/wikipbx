# INSTRUCTIONS
# 1. Change DATABASE_USER
# 2. Change DATABASE_PASSWORD
# 3. Customize FREESWITCH_URL_PORT

import os
import tempfile

# settings.py lives in the wikipbx subdir, eg, the "source" directory
# (/usr/src/wikipbx/wikipbx)
INSTALL_SRC = os.path.abspath(os.path.dirname(__file__))

# the parent of the source directory is the installation root, eg, the
# dir the user checked out to (eg, /usr/src/wikipbx)
INSTALL_ROOT = os.path.split(INSTALL_SRC)[0]

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = 'wikipbx'             # Or path to database file if using sqlite3.
DATABASE_USER = 'YOUR_DB_USER'             # Not used with sqlite3.
DATABASE_PASSWORD = 'YOUR_DB_PASS'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = '/site_media/'

# URL that handles the soundclips media.
SOUNDCLIPS_MEDIA_URL = '/soundclips_media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '_#5%!uu1rgn9qu80ewht&8y96lqu2_r9s09*g(94$smx#xc*!o'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)

ROOT_URLCONF = 'wikipbx.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(INSTALL_SRC, "wikipbxweb/templates"),
    os.path.join(INSTALL_SRC, "freeswitchxml"),
    os.path.join(INSTALL_SRC, "contacts/templates"),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'wikipbx.wikipbxweb',
    'wikipbx.contacts',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.media',
    'wikipbx.wikipbxweb.context_processors.soundclips_media_processor',
    'wikipbx.wikipbxweb.context_processors.global_processor',
)

AUTH_PROFILE_MODULE = 'wikipbxweb.UserProfile' 

STATIC_TTS_ENGINE = "cepstral"

# Installed Cepstral voices
TTS_VOICE_CHOICES = [(voice, voice) for voice in ('Allison', 'Mila', 'William')]

# Default TTS voice
TTS_DEFAULT_VOICE = 'William'


# you must manually create directories and subdirectories, eg:
# mkdir -p /var/log/wikipbx/cdr/err 
# and set permissions according to user freeswitch process will run under
LOG_DIR_ROOT = "/var/log/wikipbx"
CDR_LOG_DIR = os.path.join(LOG_DIR_ROOT, "cdr")
CDR_ERR_LOG_DIR = os.path.join(LOG_DIR_ROOT, "cdr", "err")

# should the entire raw cdr xml be saved in the db?  (uses lots of db
# space but useful when the extracted fields aren't enough information)
CDR_SAVE_XML = False

# the url (including port if non-default) where freeswitch can contact
# the wikipbx server for things like posting XML_CDR records.
# this value completely depends on how you have your webserver
# setup.  Can be ip or hostname, depends on webserver
FREESWITCH_URL_PORT = "http://127.0.0.1"

# Set to True to enabled DB administration interface.
ENABLE_DB_ADMIN = False

TEMP_DIR = tempfile.gettempdir()
