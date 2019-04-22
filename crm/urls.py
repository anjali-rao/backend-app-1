from django.urls import path

from crm.views import (
    GetQuotes, QuoteDetails, QuotesComparision, GetRecommendatedQuotes)

urlpatterns = [
    path('quote/<int:pk>', QuoteDetails.as_view()),
    path('quotes', GetQuotes.as_view()),
    path('quotes/compare', QuotesComparision.as_view()),
    path('quotes/recommendation', GetRecommendatedQuotes.as_view()),
]