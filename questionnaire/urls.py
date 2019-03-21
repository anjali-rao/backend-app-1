from django.conf.urls import url

from questionnaire.views import (
    GetQuestionnaire
)

urlpatterns = [
    url(r'user/questionnaire$', GetQuestionnaire.as_view())
]
