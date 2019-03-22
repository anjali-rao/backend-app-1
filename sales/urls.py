from django.conf.urls import url

from sales.views import (
    GetQuotes, CreateApplication)

urlpatterns = [
    url(r'lead/quotes$', GetQuotes.as_view()),
    url(r'lead/application/create$', CreateApplication.as_view()),
]
