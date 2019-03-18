from django.core.exceptions import ImproperlyConfigured

import json
import os
import redis

CONFIGURATION_FILE = os.environ.get('GOPLANNR_CONFIG')

if CONFIGURATION_FILE is None:
    raise ImproperlyConfigured(
        "ImproperlyConfigured: Set CONFIG environment variable"
    )


with open(CONFIGURATION_FILE) as f:
    configs = json.loads(f.read())


def get_env_var(setting, configs=configs):
    try:
        return configs[setting]
    except KeyError:
        raise ImproperlyConfigured(
            "ImproperlyConfigured: Set {0} environment variable".format(
                setting)
        )


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = get_env_var('DEBUG')

AUTH_USER_MODEL = 'users.User'

BROKER_URL = get_env_var('BROKER_URL')
REDIS_POOL = redis.ConnectionPool.from_url(BROKER_URL)

STATIC_URL = '/static/'

SECRET_KEY = get_env_var('SECRET_KEY')
JWT_SECRET = get_env_var('JWT_SECRET')

ROOT_URLCONF = 'goplannr.urls'

ALLOWED_HOSTS = get_env_var('ALLOWED_HOSTS').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'users',
    'payment',
    'activity',
    'content',
    'crm',
    'product',
    'sales'
    # 'raven.contrib.django.raven_compat',
    # 'django_hosts',
]

# RAVEN_CONFIG = get_env_var('RAVEN_CONFIG')

if DEBUG:
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, "static"),
    ]
else:
    STATIC_ROOT = "static"


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'goplannr.wsgi.application'


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR + '/media'

DATABASES = {
    'default': {
        'ENGINE': get_env_var('DB_ENGINE'),
        'NAME': get_env_var('DB_NAME'),
        'USER': get_env_var('DB_USER'),
        'PASSWORD': get_env_var('DB_PASSWORD'),
        'HOST': get_env_var('DB_HOST'),
        'PORT': get_env_var('DB_PORT'),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',   # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',   # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',   # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',   # noqa
    },
]


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Email COnfigurations
EMAIL_USE_TLS = get_env_var('EMAIL_USE_TLS')
EMAIL_BACKEND = get_env_var('EMAIL_BACKEND')
EMAIL_HOST = get_env_var('EMAIL_HOST')
EMAIL_HOST_USER = get_env_var('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_env_var('EMAIL_HOST_PASSWORD')
EMAIL_PORT = get_env_var('EMAIL_PORT')
DEFAULT_FROM_EMAIL = get_env_var('DEFAULT_FROM_EMAIL')

# Celery Confgurations
CELERY_TIMEZONE = get_env_var('CELERY_TIMEZONE')
CELERY_ACCEPT_CONTENT = get_env_var('CELERY_ACCEPT_CONTENT').split(',')
CELERY_TASK_SERIALIZER = get_env_var('CELERY_TASK_SERIALIZER')
CELERY_RESULT_SERIALIZER = get_env_var('CELERY_RESULT_SERIALIZER')
CELERY_DEFAULT_QUEUE = get_env_var('CELERY_DEFAULT_QUEUE')

# Caching Configurations
CACHES = get_env_var('CACHING')

# SMS API KEY
SMS_API_KEY = get_env_var('SMS_API_KEY')
SMS_API = get_env_var('SMS_API')
