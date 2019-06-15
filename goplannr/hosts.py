from django.conf import settings
from django_hosts import patterns, host

host_patterns = patterns(
    '',
    host(r'api', 'goplannr.apis_urls', name='api'),
    host(r'swagger', 'goplannr.swagger_url', name='swagger'),
    host(r'payment', 'aggregator.urls', name='payment'),
    host(r'admin', settings.ROOT_URLCONF, name='admin'),
    host(r'www', settings.ROOT_URLCONF, name='www')
)
