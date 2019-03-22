from django.conf.urls import url

from questionnaire.views import (
    GetQuestionnaire, RecordQuestionnaireResponse
)

urlpatterns = [
    url(r'user/questionnaire$', GetQuestionnaire.as_view()),
    url(r'user/questionnaire/record$', RecordQuestionnaireResponse.as_view())
]
