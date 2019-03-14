def get_choices(choice_type):
    return tuple([(x, x) for x in choice_type])


def get_upload_path(instance, filename):
    return 'media/documents/{0}/{1}'.format(instance.doc_type, filename)
