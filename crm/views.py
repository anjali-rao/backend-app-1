# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, exceptions

from users.decorators import UserAuthentication
from crm.models import Lead
from crm.serializers import (
    QuoteSerializer, QuoteDetailsSerializer, Quote,
    QuotesCompareSerializer, QuoteRecommendationSerializer
)

from utils.mixins import APIException

from django.db import transaction, IntegrityError


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
            return queryset.order_by('premium')
        raise exceptions.NotFound("No Quotes found for given lead.")


class QuoteDetails(generics.RetrieveAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuoteDetailsSerializer
    queryset = Quote.objects.all()


class QuotesComparision(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuotesCompareSerializer

    def get_queryset(self):
        try:
            lead = Lead.objects.get(id=self.request.query_params.get('lead'))
        except Lead.DoesNotExist:
            raise exceptions.NotFound('Lead doesnot exists')
        if not self.request.query_params.get('quotes') or len(
                self.request.query_params['quotes'].split(',')) < 2:
            raise exceptions.NotAcceptable(
                'Atleast two quotes are required for comparision')
        return lead.get_quotes().filter(
            id__in=self.request.query_params['quotes'].split(','))


class GetRecommendatedQuotes(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuoteRecommendationSerializer

    def get_queryset(self):
        try:
            with transaction.atomic():
                lead = Lead.objects.get(
                    id=self.request.query_params.get('lead'))
                if self.request.query_params.get('suminsured'):
                    lead.final_score = self.request.query_params['suminsured']
                    lead.save()
                elif self.request.query_params.get('reset'):
                    lead.calculate_final_score()
                return lead.get_recommendated_quotes()
        except Lead.DoesNotExist:
            raise exceptions.NotFound('Lead doesnot exists')
        except IntegrityError:
            pass
        raise APIException(
            'Curently we are unable to suggest any quote. please try again.')
