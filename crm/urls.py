from django.urls import path

from crm.views import (
    GetQuotes, QuoteDetails, QuotesComparision, GetRecommendatedQuotes,
    CreateLead, UpdateLead, GetLeadDetails, AddLeadNotes)

urlpatterns = [
    path('quote/<int:pk>', QuoteDetails.as_view()),
    path('quotes', GetQuotes.as_view()),
    path('quotes/compare', QuotesComparision.as_view()),
    path('quotes/recommendation', GetRecommendatedQuotes.as_view()),
    path('lead/create', CreateLead.as_view()),
    path('lead/<int:pk>', GetLeadDetails.as_view()),
    path('lead/<int:pk>/update', UpdateLead.as_view()),
    path('lead/<int:pk>/notes/create', AddLeadNotes.as_view()),
]
