from django.conf import settings
from django_hosts import patterns, host

host_patterns = patterns(
    '',
    host(r'api', 'goplannr.apis_urls', name='api'),
    host(r'admin', settings.ROOT_URLCONF, name='admin'),
    host(r'www', settings.ROOT_URLCONF, name='www')
)
