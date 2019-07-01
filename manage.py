#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "goplannr.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        try:
            import django # noqa
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    if 'send_report' in sys.argv:
        import requests
        with open('.circleci/test_report.log', 'rb') as report:
            requests.post(
                "https://hooks.slack.com/services/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", # noqa
                json=dict(text=report.read()))
    else:
        execute_from_command_line(sys.argv)
