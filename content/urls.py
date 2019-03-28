from django.conf.urls import url

from content.views import (
    GetFaq
)

urlpatterns = [
    url(r'faq$', GetFaq.as_view())
]
