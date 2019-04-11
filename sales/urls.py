from django.urls import path

from sales.views import (
    CreateApplication
)

urlpatterns = [
    path('lead/application/create', CreateApplication.as_view()),
]
