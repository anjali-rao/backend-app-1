# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, status
from rest_framework.response import Response

from users.decorators import UserAuthentication
from questionnaire.serializers import (
    QuestionnSerializers, Question, ResponseSerializer,
    QuestionnaireResponseSerializer
)
from sales.serializers import QuoteSerializers


class GetQuestionnaire(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuestionnSerializers

    def get_queryset(self):
        return Question.objects.filter(
            category_id=self.request.query_params.get('category'))


class RecordQuestionnaireResponse(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = ResponseSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead = self.create_lead(
            serializer.data['category_id'], serializer.data['family'],
            serializer.data['pincode'], serializer.data['customer_segment_id'])
        for response in serializer.data['answers']:
            ans_serializer = QuestionnaireResponseSerializer(
                data=response)
            ans_serializer.is_valid(raise_exception=True)
            ans_serializer.save(lead_id=lead.id)
        lead.calculate_final_score()
        return Response(QuoteSerializers(
            lead.get_quotes(), many=True).data, status=status.HTTP_201_CREATED)

    def create_lead(self, category_id, family, pincode, customer_segment_id):
        from crm.models import Lead
        return Lead.objects.create(
            user_id=self.request.user.id, family=family, pincode=pincode,
            category_id=category_id, customer_segment_id=customer_segment_id)
