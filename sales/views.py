# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, exceptions

from users.decorators import UserAuthentication
from sales.serializers import (
    QuoteSerializer, Quote, CreateApplicationSerializer,
    QuotesDetailsSerializer, CompareSerializer
)

from crm.models import Lead


class GetQuotes(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuoteSerializer

    def get_queryset(self):
        try:
            lead = Lead.objects.get(id=self.request.query_params.get('lead'))
        except Lead.DoesNotExist:
            raise exceptions.NotFound('Lead doesnot exists')
        if 'suminsured' in self.request.query_params:
            lead.final_score = self.request.query_params['suminsured']
            lead.save()
        queryset = lead.get_quotes()
        if queryset.exists():
            return queryset
        raise exceptions.NotFound("No Quotes found for given lead.")


class CreateApplication(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CreateApplicationSerializer


class QuotesDetails(generics.RetrieveAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuotesDetailsSerializer
    queryset = Quote.objects.all()


class CompareRecommendation(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CompareSerializer

    def get_queryset(self):
        try:
            lead = Lead.objects.get(id=self.request.query_params.get('lead'))
        except Lead.DoesNotExist:
            raise exceptions.NotFound('Lead doesnot exists')
        if not self.request.query_params.get('quotes') or len(
                self.request.query_params['quotes'].split(',')) < 2:
            raise exceptions.NotAcceptable(
                'Atlest two quotes are required for comparision')
        return lead.get_quotes().filter(
            id__in=self.request.query_params['quotes'].split(','))
