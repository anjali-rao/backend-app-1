from django.urls import path

from sales.views import (
    CreateApplication, RetrieveUpdateProposerDetails,
    RetrieveUpdateApplicationMembers, CreateApplicationNominee,
    UpdateInsuranceFields, ApplicationSummary, CreateExistingPolicies,
    GetInsuranceFields, SubmitApplication
)

urlpatterns = [
    path('application/create', CreateApplication.as_view()),
    path('application/<int:pk>/contact', RetrieveUpdateProposerDetails.as_view()), # noqa
    path('application/<int:pk>/members', RetrieveUpdateApplicationMembers.as_view()), # noqa
    path('application/<int:pk>/nominee', CreateApplicationNominee.as_view()), # noqa
    path('application/<int:pk>/insurance/update', UpdateInsuranceFields.as_view()), # noqa
    path('application/<int:pk>/insurance/fields', GetInsuranceFields.as_view()), # noqa
    path('application/<int:pk>/policies', CreateExistingPolicies.as_view()),
    path('application/<int:pk>/summary', ApplicationSummary.as_view()),
    path('application/<int:pk>/submit', SubmitApplication.as_view())
]
