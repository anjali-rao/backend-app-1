from __future__ import absolute_import

from celery.schedules import crontab

TASKS = {
    'half-hourly-sms-analysis': {
        'task': 'users.tasks.analyze_smses',
        'schedule': crontab(minute="*/10", hour="*"),
    }
}
