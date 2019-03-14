from django.conf.urls import url, include

urlpatterns = [
    url(r'^(?P<version>(v1))/', include('users.urls')),
]
