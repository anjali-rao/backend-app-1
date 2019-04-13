from django.urls import path

from sales.views import (
    CreateApplication, RetrieveUpdateProposerDetails
)

urlpatterns = [
    path('application/create', CreateApplication.as_view()),
    path('application/<int:pk>/contact', RetrieveUpdateProposerDetails.as_view()), # noqa
]
