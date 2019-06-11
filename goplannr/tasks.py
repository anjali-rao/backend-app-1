from __future__ import absolute_import

from celery.schedules import crontab

TASKS = {
    'daily_mark_ignore_rejected_quotes': {
        'task': 'sales.tasks.mark_ignore_rejected_quotes',
        'schedule': crontab(hour=15, minute=30),
    }
}
