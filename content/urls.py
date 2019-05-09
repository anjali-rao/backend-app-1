from django.urls import path

from content.views import (
    GetFaq, ContactUsAPI, AddNewsLetterSubscriber
)
from content.views import AddPromotion


urlpatterns = [
    path('faq', GetFaq.as_view()),
    path('contact-us', ContactUsAPI.as_view()),
    path('newsletter', AddNewsLetterSubscriber.as_view()),
    path('submit-phone', AddPromotion.as_view())
]
