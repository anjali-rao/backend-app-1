from django.urls import path

from sales.views import (
    GetQuotes, CreateApplication, QuotesDetails,
    CompareRecommendation, GetRecommendatedQuotes)

urlpatterns = [
    path('quote/<int:pk>', QuotesDetails.as_view()),
    path('quotes', GetQuotes.as_view()),
    path('quotes/recommendation', GetRecommendatedQuotes.as_view()),
    path('quotes/compare', CompareRecommendation.as_view()),
    path('lead/application/create', CreateApplication.as_view()),
]
