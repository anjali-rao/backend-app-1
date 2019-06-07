from django.core.exceptions import ImproperlyConfigured

import json
import os


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
