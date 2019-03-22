# GoPlannr Backend
=============================================================================================================================

## Setting up development environment

The development environment can be setup either like a pythonista
with the usual python module setup, or like a docker user.

### The pythonista way

Ensure that you have an updated version of pip

```
pip --version
```
Should atleast be 1.5.4

If pip version is less than 1.5.4 upgrade it
```
pip install -U pip
```

This will install latest pip

Ensure that you are in virtualenv
if not install virtual env
```
sudo pip install virtualenv
```
This will make install all dependencies to the virtualenv
not on your root

From the module folder install the dependencies. This also installs
the module itself in a very pythonic way.

```
pip install -r requirements.txt
```
## NOTE
export the configuration file after setup
```
export GOPLANNR_CONFIG='/home/<user>/configurations/goplannr.json'
```
Configuration file

```
{
    "SECRET_KEY" : <SECRET_KEY>,
    "JWT_SECRET": <JWT_SECRET_KEY>,
    "DEBUG" : <DEBUG>,
    "ALLOWED_HOSTS": "*",
    "DB_ENGINE": "django.db.backends.postgresql_psycopg2",
    "DB_NAME": "<db_name>",
    "DB_USER": <db_username>,
    "DB_PASSWORD": <db_password>,
    "DB_HOST": "<db_host>",
    "DB_PORT": "<db_port>,
    "BROKER_URL": "<broker_url>",
    "EMAIL_USE_TLS": true,
    "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    "EMAIL_HOST": <email_host>,
    "EMAIL_HOST_USER": <email_port>,
    "DEFAULT_FROM_EMAIL": <default_email>,
    "EMAIL_HOST_PASSWORD": <app_password>,
    "EMAIL_PORT": <email_port>,
    "CELERY_TIMEZONE": "Asia/Kolkata",
    "CELERY_ACCEPT_CONTENT": "json,",
    "CELERY_TASK_SERIALIZER": "json",
    "CELERY_RESULT_SERIALIZER": "json",
    "CELERY_DEFAULT_QUEUE": "celery",
    "CACHING": {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://127.0.0.1:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient"
            },
            "KEY_PREFIX": "goplanr"
        }
    },
    "SMS_API": "<sms_api",
    "SMS_API_KEY": "<sms_api_key>",
    "DEBUG_HOST": "<debug_host>",
    "PRODUCTTION_HOST": "<production_host>"
}


```


Before begining you need to migrate tables

Perform migration by
```
python manage.py makemigrations
python manage.py migrate
```

and then create a superuser as no user is currently present in the database and apis require authentication(i.e username and password)

```
Python manage.py createsuperuser
```

Run app by
```
python manage.py runserver
```

For any clarification regarding setup refer Amit