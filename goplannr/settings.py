import os
import redis
from goplannr.configuration import get_env_var

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = get_env_var('DEBUG')

AUTH_USER_MODEL = 'users.Account'

BROKER_URL = get_env_var('BROKER_URL')
REDIS_POOL = redis.ConnectionPool.from_url(BROKER_URL)

STATIC_URL = '/static/'

SECRET_KEY = get_env_var('SECRET_KEY')
JWT_SECRET = get_env_var('JWT_SECRET')

ENV = get_env_var('ENV')

DEFAULT_HOST = "www"
ROOT_HOSTCONF = 'goplannr.hosts'
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
    'corsheaders',
    'django_hosts',
    'users',
    'payment',
    'activity',
    'content',
    'crm',
    'product',
    'sales',
    'questionnaire',
    'aggregator.wallnut',
    'earnings'
]

if DEBUG:
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, "static"),
    ]
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR + '/media'
else:
    STATIC_ROOT = "static"
    RAVEN_CONFIG = get_env_var('RAVEN_CONFIG')
    INSTALLED_APPS.extend(['raven.contrib.django.raven_compat', 'storages'])
    # For S3 Document Stroage
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    CLOUDFRONT_DOMAIN = get_env_var('CLOUDFRONT_DOMAIN')
    CLOUDFRONT_ID = get_env_var('CLOUDFRONT_ID')
    AWS_STORAGE_BUCKET_NAME = get_env_var('S3_BUCKET')
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    AWS_ACCESS_KEY_ID = get_env_var('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = get_env_var('AWS_SECRET_ACCESS_KEY')
    MEDIA_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
    MEDIA_ROOT = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
    AWS_AUTO_CREATE_BUCKET = True

MIDDLEWARE = [
    'django_hosts.middleware.HostsRequestMiddleware',
    'goplannr.whiteListingMiddleware.AuthIPWhitelistMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware'
]

CORS_ORIGIN_ALLOW_ALL = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'users/templates'),
        ],
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
SMS_OTP_HASH = get_env_var('SMS_OTP_HASH')

# REST_FRAMEWORK

REST_FRAMEWORK = dict(
    EXCEPTION_HANDLER='utils.mixins.custom_exception_handler'
)
