from django.utils.crypto import get_random_string


def get_choices(choice_type, extra=None):
    choices = [(x, x.replace('_', ' ').title()) for x in choice_type]
    if extra:
        choices.append((extra, extra))
    return tuple(choices)


def get_upload_path(instance, filename):
    return 'documents/{0}/{1}/{2}'.format(
        instance.contact.id, instance.document_type, filename)


def get_kyc_upload_path(instance, filename):
    return 'user/{0}/kyc/{1}/{2}'.format(
        instance.account.id, instance.document_type, filename)


def get_proposer_upload_path(instance, filename):
    return 'proposer/{0}/documents/{1}/{2}'.format(
        instance.contact.id, instance.document_type, filename)


def genrate_random_string(length):
    return get_random_string(
        length,
        allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789')
