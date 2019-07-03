from django.urls import path

from content.views import (
    GetFaq, ContactUsAPI, AddNewsLetterSubscriber,
    GetNetworkHospital, GetHelpFiles, GetHelpLines,
    GetCollateral
)
from content.views import AddPromotion


urlpatterns = [
    path('faq', GetFaq.as_view()),
    path('contact-us', ContactUsAPI.as_view()),
    path('newsletter', AddNewsLetterSubscriber.as_view()),
    path('submit-phone', AddPromotion.as_view()),
    path('networkhospital', GetNetworkHospital.as_view()),
    path('helpfiles', GetHelpFiles.as_view()),
    path('helplines', GetHelpLines.as_view()),
    path('collaterals', GetCollateral.as_view()),
]
