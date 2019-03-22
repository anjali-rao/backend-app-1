from django.conf.urls import url

from sales.views import GetQuotes

urlpatterns = [
    url(r'user/product/quotes$', GetQuotes.as_view()),
]
