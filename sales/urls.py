from django.urls import path

from sales.views import (
    CreateApplication, RetrieveUpdateProposerDetails,
    RetrieveUpdateApplicationMembers, CreateApplicationNominee
)

urlpatterns = [
    path('application/create', CreateApplication.as_view()),
    path('application/<int:pk>/contact', RetrieveUpdateProposerDetails.as_view()), # noqa
    path('application/<int:pk>/members', RetrieveUpdateApplicationMembers.as_view()), # noqa
    path('application/<int:pk>/nominee', CreateApplicationNominee.as_view()), # noqa

]
