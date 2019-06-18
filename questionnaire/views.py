# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, status, exceptions
from rest_framework.response import Response

from users.decorators import UserAuthentication
from questionnaire.serializers import (
    QuestionnSerializers, Question, ResponseSerializer,
    QuestionnaireResponseSerializer
)
from utils.mixins import APIException
from crm.serializers import (
    QuoteRecommendationSerializer, Opportunity)
from django.db import transaction, IntegrityError


class GetQuestionnaire(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuestionnSerializers

    def get_queryset(self):
        questionnaire = Question.objects.filter(
            category_id=self.request.query_params.get('category'),
            ignore=False)
        if not questionnaire:
            raise exceptions.NotFound(
                'No Questionnaire found for given category id')
        return questionnaire


class RecordQuestionnaireResponse(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = ResponseSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                from questionnaire.models import Response as QuestionResponse
                opportunity = Opportunity.objects.get(
                    id=serializer.data['opportunity_id'])
                QuestionResponse.objects.filter(
                    opportunity_id=opportunity.id).delete()
                for response in serializer.data['answers']:
                    ans_serializer = QuestionnaireResponseSerializer(
                        data=response)
                    ans_serializer.is_valid(raise_exception=True)
                    ans_serializer.save(opportunity_id=opportunity.id)
                opportunity.calculate_suminsured()
            return Response(
                QuoteRecommendationSerializer(
                    opportunity.get_recommendated_quotes(), many=True).data,
                status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            print(e)
            pass
        raise APIException(
            'Unable to process request currently. Please try again')
