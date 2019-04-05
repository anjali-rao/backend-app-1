from django.utils.crypto import get_random_string


def get_choices(choice_type, extra=None):
    choices = [(x, x) for x in choice_type]
    if extra:
        choices.append((extra, extra))
    return tuple(choices)


def get_upload_path(instance, filename):
    return 'documents/{0}/{1}'.format(instance.doc_type, filename)


def get_kyc_upload_path(instance, filename):
    return 'kyc/{0}/{1}'.format(instance.doc_type, filename)


def genrate_random_string(length):
    return get_random_string(
        length,
        allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789')
