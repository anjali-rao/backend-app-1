from django.conf.urls import url, include

urlpatterns = [
    url(r'^(?P<version>(v1|v2))/', include('users.urls')),
    url(r'^(?P<version>(v1|v2))/', include('product.urls')),
    url(r'^(?P<version>(v1|v2))/', include('questionnaire.urls')),
    url(r'^(?P<version>(v1|v2))/', include('sales.urls')),
]
