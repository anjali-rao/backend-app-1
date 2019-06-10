from __future__ import absolute_import

import os
from celery import Celery
from raven import Client
from raven.contrib.celery import register_signal, register_logger_signal
from .configuration import get_env_var


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goplannr.settings')


class Celery(Celery):

    def on_configure(self):
        if not get_env_var('DEBUG'):
            client = Client(get_env_var('RAVEN_CONFIG')['dsn'])
            register_logger_signal(client)
            register_signal(client)


app = Celery('goplannr')
app.config_from_object('django.conf:settings')
app.autodiscover_tasks()
