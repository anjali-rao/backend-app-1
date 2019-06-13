# GoPlannr Backend
===============================================================================

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

Configuration file or utils/sample_configuration_file.json

```
{
    "SECRET_KEY" : <SECRET_KEY>,
    "DEBUG": true,
    "ALLOWED_HOSTS": "*",
    "DB_ENGINE": "django.db.backends.postgresql_psycopg2",
    "DB_NAME": "<db_name>",
    "DB_USER": <db_username>,
    "DB_PASSWORD": <db_password>,
    "DB_HOST": "<db_host>",
    "DB_PORT": "<db_port>,
    "JWT_SECRET": <JWT_SECRET_KEY>,
    "BROKER_URL": "redis://localhost:6379/0", //Install redis-server
    "EMAIL_USE_TLS": true,
    "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    "EMAIL_HOST": "",
    "EMAIL_HOST_USER": "",
    "DEFAULT_FROM_EMAIL": "",
    "EMAIL_HOST_PASSWORD": "",
    "EMAIL_PORT": "",
    "CELERY_TIMEZONE": "Asia/Kolkata",
    "CELERY_ACCEPT_CONTENT": "json,pickle",
    "CELERY_TASK_SERIALIZER": "pickle",
    "CELERY_RESULT_SERIALIZER": "pickle",
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
    "SMS_API": "https://alerts.solutionsinfini.com/api/v4/?api_key=",
    "SMS_API_KEY": "<SMS_API_KEY>",
    "DEFAULT_HOST": "http://localhost:8000",
    "PRODUCTTION_HOST": "http://api.goplannr.com",
    "S3_BUCKET": "develop-goplannr" 
    "RAVEN_CONFIG": {
        "dsn": "https://6037e72fa5534db6bf38e4b48e08f1f0@sentry.io/1427326"
    },
    "AWS_ACCESS_KEY_ID": ''>,
    "AWS_SECRET_ACCESS_KEY": "",
    "S3_BUCKET": "staging-goplannr",
    "CLOUDFRONT_ID": "",
    "CLOUDFRONT_DOMAIN": "",
    "ENV": "localhost:8000",
    "SMS_OTP_HASH": "XTmeqjNJd+R"
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

For any clarification regarding setup refer admin

### NOTE
1. For running the server, make sure you install Redis-server on system and keep debug always as True.

2. run celery by in a seprate terminal or create a service for celery
```
celery -A goplannr worker -l info
```

### HOW TO COLLABORATE

1. Fork the repo in your's github account.
2. Clone foked repo in your local env
3. Add remote name goplannr with https://github.com/goplannr/backend-app.git
    ```
    git remote add goplannr https://github.com/goplannr/backend-app.git
    ```
4. Create a new branch with 
    ```
    git fetch goplannr develop:<your branch name>
    ```
    This will create a new branch with latest commit reference from develop(goplannr remote)
5. Checkout to new branch created
6. Make changes and commit
7. Push to your fork
    ```
    git push origin <branch name>
    ```
8. Create a PR to develop and add reviewer
9. Reviewer approve the PR and PR will be merged twice a day(11:00 AM and 7:00 PM)
10. Its you responsiblity to make sure that yours PR get Approved by reviewer.
