from django.urls import path

from content.views import (
    GetFaq, ContactUsAPI
)

urlpatterns = [
    path('faq', GetFaq.as_view()),
    path('contact-us', ContactUsAPI.as_view())
]
