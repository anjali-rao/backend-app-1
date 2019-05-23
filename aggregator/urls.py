from django.urls import path

from aggregator.wallnut.views import (
    AdityaBirlaPaymentGateway, AdityaBirlaPaymentCapture,
    HDFCPaymentGateway)

urlpatterns = [
    path('health/adityabirla/<int:pk>', AdityaBirlaPaymentGateway.as_view()),
    path('health/adityabirla/capture', AdityaBirlaPaymentCapture.as_view()),
    path('health/hdfcergo/<int:pk>', HDFCPaymentGateway.as_view()),
]
