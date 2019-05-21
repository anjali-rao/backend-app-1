from django.urls import path

from aggregator.wallnut.views import AdityaBirla, AdityaBirlaPaymentCapture

urlpatterns = [
    path('health/adityabirla/<int:pk>', AdityaBirla.as_view()),
    path('health/adityabirla/capture', AdityaBirlaPaymentCapture.as_view()),
]
