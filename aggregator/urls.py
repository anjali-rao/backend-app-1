from django.urls import path

from aggregator.wallnut.views import AdityaBirla, AdityaBirlaPayment

urlpatterns = [
    path('adityabirla/<int:pk>', AdityaBirla.as_view()),
    path('adityabirla/capture', AdityaBirlaPayment.as_view()),
]
