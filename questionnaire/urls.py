from django.urls import path

from questionnaire.views import (
    GetQuestionnaire, RecordQuestionnaireResponse
)

urlpatterns = [
    path('user/questionnaire', GetQuestionnaire.as_view()),
    path('user/questionnaire/record', RecordQuestionnaireResponse.as_view())
]
