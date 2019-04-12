from django.urls import path

from sales.views import (
    CreateApplication, GetContactDetails, UpdateContactDetails
)

urlpatterns = [
    path('lead/application/create', CreateApplication.as_view()),
    path('lead/application/<int:pk>/contact', GetContactDetails.as_view()),
    path('lead/application/contact/<int:pk>/update', UpdateContactDetails.as_view()) # noqa
]
