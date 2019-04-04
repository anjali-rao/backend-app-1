from django.urls import path

from content.views import (
    GetFaq
)

urlpatterns = [
    path('faq', GetFaq.as_view())
]
