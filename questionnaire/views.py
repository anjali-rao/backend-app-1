# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics

from users.decorators import UserAuthentication
from questionnaire.serializers import QuestionnaireSerializers, Question


class GetQuestionnaire(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuestionnaireSerializers

    def get_queryset(self):
        return Question.objects.filter(
            category_id=self.request.query_params.get('category'))
