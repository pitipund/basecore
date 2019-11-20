#!/usr/bin/python
# -*- coding: utf-8 -*-
import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))

ALLOWED_HOSTS = ['channel.penta-tv.com', 'penta.center',
                 'www.penta.center', '127.0.0.1', '192.168.6.127']

DEBUG = True

OPTIMIZE = False

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
    ('Natt', 'natt@thevcgroup.com'),
    ('Napat', 'napat@thevcgroup.com'),
    ('Sajja', 'sajja@thevcgroup.com'),
)
ADMIN_EMAILS = [a[1] for a in ADMINS]
# admins who monitor bad channel
MONITOR_ADMIN = (
    ('Napat', 'napat@thevcgroup.com'),
    ('Kulchalee', 'kulchalee@thevcgroup.com'),
    ('Pitipund', 'pitipund@thevcgroup.com'),
    ('Dr Jay', 'drjay@thevcgroup.com'),
    ('Narumon', 'narumon@thevcgroup.com'),
    ('Sajja', 'sajja@thevcgroup.com'),
)
MONITOR_ADMIN_EMAILS = [a[1] for a in MONITOR_ADMIN]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'showtime',  # Or path to database file if using sqlite3.
        'USER': 'root',  # Not used with sqlite3.
        'PASSWORD': 'powerall',  # Not used with sqlite3.
        'HOST': '',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'  # default language
ugettext = lambda s: s
LANGUAGES = (
    ('th', u'ไทย'),
    ('en', u'English'),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale/'),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'
# Override bt Minio

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'cgu#j5agb$3^7z&amp;$@zzvc)gjt2vhx!*9@_7nd@-+kj+0gg+u)w'


MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django_cas.middleware.CASMiddleware',  # ENABLECAS
    'django.middleware.locale.LocaleMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
    'channel.middleware.ForceLangMiddleware',
    #'feed.middleware.UserAccessLogger',
    # 'feed.middleware.RenderedPageForBot',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

if DEBUG:
    CORS_ORIGIN_REGEX_WHITELIST = [r'^(https?://)?(127.0.0.1|localhost):\d+$']

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'django_cas.backends.CASBackend',  # ENABLECAS
)

REST_FRAMEWORK = {  # 20 พฤษภาคม 2015, 17:27:27
    # 'DATETIME_FORMAT': (
    #     '%d %B %Y, %H:%M:%S'
    # ),
    # 'DATE_FORMAT': (
    #     '%d %B %Y'
    # ),
    # 'TIME_FORMAT': (
    #     '%H:%M:%S'
    # )
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',),
}

ROOT_URLCONF = 'showtime.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'showtime.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), MEDIA_ROOT],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                "channel.context_processors.navigation_context_values",
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
        },
    },
]


DJANGO_APPS = (
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.admin',
)

THIRD_PARTY_APPS = (
    'django_filters',
    'django_celery_results',
    'django_extensions',
    'django_user_agents',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_extensions',
    'corsheaders',
    'sorl.thumbnail',
    'minio_storage',
)

LOCAL_APPS = (
    # Local Django App
    'curator',
    'channel',
    'pentacenter',
    'apis',
    'wallpaper',
    'rating',
    'feed',
    'reports',
    'ppg',
    'appointment',
    'sqool',
    'django_cas',  # ENABLE CAS
    'extension_support',  # support for penta extension
    'videos_tagging',
    'tag_heatmap',
    'voip',
    'django_wallet_client',  # wallet alpha
    'django_facebook_messenger',
)

LOCAL_THIRD_PARTY_APPS = (
    'feed.templatetags',
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS + LOCAL_THIRD_PARTY_APPS

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
#         'LOCATION': '/tmp/cache_pentachannel',
#     }
# }
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        }
    }
}

# SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# Name of cache backend to cache user agents. If it not specified default
# cache alias will be used. Set to `None` to disable caching.
USER_AGENTS_CACHE = 'default'

#ANDROID_API_KEY = "AIzaSyB3WzJ_t5_cDhHEkqzLOAyFXHEj9PqE-E0"
ANDROID_API_KEY = "AAAAue-cMf8:APA91bHZ9f5uvCknVP9UOFucnwYYsmjRm1lBY1iadMdATISz2vvLGe4W2t_ACHYftil-zvamxMi5rxGAZBQ0lQvyg1WpMCCj_d3wAfpm5XMQSJFMDkRwhweYWD8XjbFVMrrj9UbEtcKY"

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ENABLE_UTC = False
CELERY_TIMEZONE = 'Asia/Bangkok'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'raw': {
            'format': '%(asctime)s %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'raw',
        },
        'tag_heatmap': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'raw',
        },
        'pentatv_app_auth': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'raw',
        }
    },
    'loggers': {
        'feed_utils': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['console', 'mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'showtime.push': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        'audit': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'analytic': {
            'handlers': [],
            'level': 'INFO',
            'propagate': 'True',
        },
        'terrain': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apis.views': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'apis.account_api': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'curator': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'sqool': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
        'appointment': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
        'tag_heatmap': {
            'handlers': ['tag_heatmap'],
            'level': 'DEBUG',
        },
        'tag_heatmap_per': {
            'handlers': ['tag_heatmap'],
            'level': 'DEBUG',
        },
        'pentatv_app_auth': {
            'handlers': ['pentatv_app_auth'],
            'level': 'DEBUG',
        },
        'voip': {
            'handlers': ['console'],
            'level': 'DEBUG'
        },
        # Uncomment to enable `SQL DEBUG`
        # 'django.db.backends': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG'
        # },
    }
}

DAILY_ACCESS_LOG_REPORT = "/var/log/pentachannel/access_report.json"
USER_ACCESS_LOG_REPORT = "/var/log/pentachannel/user_report.json"

DIGITAL_IP = '203.144.234.35'
DIGITAL_SERVER = DIGITAL_IP + ':8801'
DIGITAL_BLANK = DIGITAL_SERVER + '/blank/'
TAG_LIVE = 'รายการสด'

# Live Link from Charan office (for maintainance mode)
CHARAN_PATTERN = (
    'http://gatekeeper.penta-tv.com/redir/',
    'http://gatekeeper.penta.center/redir/',
)

AUTH_USER_MODEL = 'curator.User'

INVALID_URL_NAME = ['admin', 'profile', 'home', 'browse', 'channel', 'search', 'notification', 'manual', 'play',
                    'stats', 'v', 'apis']
# # CAS configuration
CAS_SERVER_URL = 'https://accounts.thevcgroup.com/cas/'
CAS_AUTO_CREATE_USERS = True
CAS_REGIS = 'https://accounts.thevcgroup.com/accounts/register/?site=penta'

# Path configuration#
IMAGES_URL = 'images'

EMAIL_PATH = 'uploaded/email'
EMAIL_TEMPLATE_PATH = 'uploaded/email_templates'
ICON_PATH = 'uploaded/icon'
THUMBNAIL_PATH = 'uploaded/thumbnail'
PROFILE_PATH = 'uploaded/profile'
ARTIST_PATH = 'uploaded/artist'
SHOW_PATH = 'uploaded/show'
DIRECTORY_PATH = 'uploaded/directory'
SQOOL_PATH = 'uploaded/sqool_content'
PREMISE_PATH = 'uploaded/premise_content'
ALBUM_PATH = 'uploaded/album'
SERVICE_APP_IMG_PATH = 'uploaded/service_appointment'

THUMBNAIL_IM_PATH = os.path.join('uploaded', 'thumbnail')
SUPPORT_IM_PATH = os.path.join('uploaded', 'support')
WALLPAPER_PATH = os.path.join('uploaded', 'wallpaper')
EXTENSION_SUPPORT_IM_PATH = os.path.join('uploaded', 'extension_support')

AUTH_PROFILE_MODULE = 'curator.UserProfile'

# Exclude live channels
EXCLUDE_CHANNELS = [3, 4, 6, 7, 8, 10, 14, 26, 27, 63, 105, 111, 112, 114, 115, 117, 118, 119, 120, 121, 122, 123, 127,
                    129, 130, 131, 133, 134, 23, 42, 49, 76, 87, 17]  # channel 7, channel 5, channel 8

STAFF_PICK_CHANNEL = 321
TAG_POPULAR_ID = 229  # special tag
TAG_NEW_CHANNEL_ID = 230  # special tag
TAG_LIVE_CHANNEL_ID = 126
CHANNEL_RESULT_AMOUNT_FROM_SPECIAL_TAG = 50
SPACIAL_LIVE_CURATOR_CHANNEL = [405, 406, 925]  # ['CNN', 'BBC', 'Fox Thai']

URL_THEVOICE_APP = 'https://play.google.com/store/apps/details?id=com.ilovemusic.ting'

VIDEO_SNAPSHOT_ENABLED = False

CACHE_TIMESPAN_IN_ROOM = 300 # seconds

DEFAULT_MAX_MEMCACHE_SIZE = 1024 * 1024 * 10 # 10mb also need to specific -I 10m to /etc/memcached.conf

# Facebook API Settings

FACEBOOK_APP_ID = '571837776208476'
FACEBOOK_APP_SECRET = 'a5f3b5ed0e4ee0bd4b6cf45e1458c208'

FACEBOOK_APP_ACCESS_TOKEN = '%s|%s' % (FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)

FACEBOOK_PAGE_ACCESS = [
    {
        'id': '205324643383386',
        'name': 'penta_dev',
        'token': 'EAAIIFVuFIlwBAJOUMdfmhXtckdfuMQYI3ZCclIPaTfcJcX7vxdHK0H6pRy'
                 'rH49nShvtgHqn71VWu9irfKLh8CtPb6xksnHZBPiuwnZBc3glVSkM1ovArq'
                 'Q2rTZCqZCA2BATPNldPqC0wRarmxtcIUWZAYrCa6aZCiQuMWiSoULf7wZDZD',
    },
    {
        'id': '215885658567078',
        'name': 'penta_tv',
        'token': 'EAAIIFVuFIlwBAIf7MBFjjYq6b0R97AnsQEXsuAMwYlXJ67LBwx5knY0P2m'
                 '8SGPawnCZC2eMfOUHIXxaoOlGpY0PvyzkHuXByTti0FI9QNAp0K5ZCFg6p7'
                 'IZBrPPv1Mn8BEWnpgaa6J0d1k8TmgwOZCeJZCALfvdH5i9QcLwW2ZBQZDZD'
    }
]

FACEBOOK_MESSENGER_HOOK_CALLBACK = {
    'penta_tv': 'sqool.webhooks.PentaTVWebhook',
    'penta_dev': 'sqool.webhooks.PentaTVWebhook',
}
FACEBOOK_HOOK_VERIFICATION = '812fc1b2-15f9-11e8-9e05-6370b95722ab'

# please update word in get_highlight.py too
BANNED_KEYWORDS = [u'หื่น', u'คราง', u'เย็ด', u'ความใคร่', u'แทง', u'เงี่ยน', u'ตูด', u'สัส', u'หี', u'ควย', u'เสียว', u'หลุด', u'ตาย', u'เสียชีวิต', u'คลิป', u'18+', u'รุมโทรม', u'sex', u'teaser', u'trailer', u'ตัวอย่าง', u'ชนเผ่าแอฟริกัน', u'มายคราฟ', u'ศพ', u'โหด', u'สัด', u'สัส', u'ทั้งเป็น', u'กระเทย', u'กินคน', u'เซ็กซ์', u'จังไร']

# Google Cloud Api
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = BASE_DIR + '/showtime/GoogleHeatmapKey_staging.json'

# Notification Settings

NOTIFICATION_CREDENTIALS = {
    'default': {
        'android': {
            'key': 'AAAAue-cMf8:APA91bHZ9f5uvCknVP9UOFucnwYYsmjRm1lBY1iadMd'
                   'ATISz2vvLGe4W2t_ACHYftil-zvamxMi5rxGAZBQ0lQvyg1WpMCCj_d'
                   '3wAfpm5XMQSJFMDkRwhweYWD8XjbFVMrrj9UbEtcKY',
        },
        'ios': {
            'cert_file': os.path.join(BASE_DIR, 'pentacenter/keys/aps-10.pem'),
            'key_file': os.path.join(BASE_DIR, 'pentacenter/keys/PentaCenter.Certificates.pem')
        },
    },
}
NOTIFICATION_APP_MAP = {
    'generic': 'default',
    'sqool': 'default',
}


# VOIP Settings
VOIP_ALLOWED_IP = ['111.223.34.85']  # addition ip for voip server (other than in VOIP server model)

# Wallet Settings
WALLET_URL = "http://127.0.0.1:8000/"
WALLET_TOKEN = "b646a5719ebe3d4039d262fbc7bdc0a595c81db5"


TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Minio settings
DEFAULT_FILE_STORAGE = 'minio_storage.storage.MinioMediaStorage'
MINIO_STORAGE_ENDPOINT = 's3.drjaysayhi.com'
MINIO_STORAGE_USE_HTTPS = False
MINIO_STORAGE_ACCESS_KEY = 'powerall'
MINIO_STORAGE_SECRET_KEY = 'MU8tXyIBE5srrw/2P2zyA1/7RsHltVjcz98in8nfmz'
MINIO_STORAGE_MEDIA_BUCKET_NAME = 'showtime-test'
MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True
MINIO_STORAGE_MEDIA_URL = 'https://cdn.drjaysayhi.com/%s/' % MINIO_STORAGE_MEDIA_BUCKET_NAME
MEDIA_URL = 'https://cdn.drjaysayhi.com/%s/' % MINIO_STORAGE_MEDIA_BUCKET_NAME
