# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics

from users.decorators import UserAuthentication
from sales.serializers import (
    QuoteSerializer, Quote, CreateApplicationSerializer,
    QuotesDetailsSerializer
)

from crm.models import Lead


class GetQuotes(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuoteSerializer

    def get_queryset(self):
        lead = Lead.objects.get(id=self.request.query_params.get('lead'))
        if 'suminsured' in self.request.query_params:
            lead.final_score = self.request.query_params['suminsured']
            lead.save()
        return lead.get_quotes()


class CreateApplication(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CreateApplicationSerializer


class QuotesDetails(generics.RetrieveAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuotesDetailsSerializer
    queryset = Quote.objects.all()
