from django.conf.urls import url

from sales.views import (
    GetQuotes, CreateApplication, QuotesDetails,
    CompareRecommendation, GetRecommendatedQuotes)

urlpatterns = [
    url(r'quote/(?P<pk>[0-9]+)$', QuotesDetails.as_view()),
    url(r'quotes$', GetQuotes.as_view()),
    url(r'quotes/recommendation$', GetRecommendatedQuotes.as_view()),
    url(r'quotes/compare$', CompareRecommendation.as_view()),
    url(r'lead/application/create$', CreateApplication.as_view()),
]
