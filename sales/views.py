# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, exceptions, status
from rest_framework.response import Response

from users.decorators import UserAuthentication
from sales.serializers import (
    QuoteSerializer, Quote, CreateApplicationSerializer,
    QuotesDetailsSerializer, CompareSerializer, RecommendationSerializer
)

from crm.models import Lead
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
                'Atleast two quotes are required for comparision')
        return lead.get_quotes().filter(
            id__in=self.request.query_params['quotes'].split(','))


class GetRecommendatedQuote(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = RecommendationSerializer

    def get_queryset(self):
        try:
            with transaction.atomic():
                lead = Lead.objects.get(
                    id=self.request.query_params.get('lead'))
                if self.request.query_params.get('suminsured'):
                    lead.final_score = self.request.query_params['suminsured']
                    lead.save()
                else:
                    lead.calculate_final_score()
                lead.get_recommendated_quote()
                return Response(
                    RecommendationSerializer(
                        lead.get_recommendated_quote()).data,
                    status=status.HTTP_201_CREATED)
        except Lead.DoesNotExist:
            raise exceptions.NotFound('Lead doesnot exists')
        except IntegrityError:
            raise exceptions.APIException(
                'No recommendated Quote found for given suminsured')
        except Exception:
            raise exceptions.APIException(
                'Curently we are unable to suggest any quote. please try again.') # noqa
