from django.urls import path

from content.views import (
    GetFaq, ContactUsAPI, AddNewsLetterSubscriber
)

urlpatterns = [
    path('faq', GetFaq.as_view()),
    path('contact-us', ContactUsAPI.as_view()),
    path('newsletter', AddNewsLetterSubscriber.as_view())
]
