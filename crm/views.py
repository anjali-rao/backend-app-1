# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics
from utils import mixins, constants

from users.decorators import UserAuthentication
from crm.models import Lead
from crm.serializers import (
    QuoteSerializer, QuoteDetailsSerializer, Quote,
    QuotesCompareSerializer, QuoteRecommendationSerializer,
    CreateUpdateLeadSerializer
)

from django.db import transaction, IntegrityError


class CreateLead(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CreateUpdateLeadSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save(user_id=self.request.user.id)


class UpdateLead(generics.UpdateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CreateUpdateLeadSerializer
    queryset = Lead.objects.all()


class GetQuotes(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuoteSerializer

    def get_queryset(self):
        try:
            lead = Lead.objects.get(id=self.request.query_params['lead'])
            if 'suminsured' in self.request.query_params:
                lead.final_score = self.request.query_params['suminsured']
                lead.save()
            queryset = lead.get_quotes()
            if not queryset.exists():
                raise mixins.NotFound(constants.NO_QUOTES_FOUND)
            return queryset
        except (KeyError, Lead.DoesNotExist):
            raise mixins.APIException(constants.LEAD_ERROR)
        except ValueError:
            raise mixins.APIException(constants.INVALID_INPUT)


class QuoteDetails(generics.RetrieveAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuoteDetailsSerializer
    queryset = Quote.objects.all()


class QuotesComparision(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuotesCompareSerializer

    def get_queryset(self):
        try:
            lead = Lead.objects.get(id=self.request.query_params['lead'])
            if not self.request.query_params.get('quotes') or len(
                    self.request.query_params['quotes'].split(',')) < 2:
                raise mixins.NotAcceptable(constants.COMPARISION_ERROR)
            quotes_ids = self.request.query_params['quotes'].split(',')
            queryset = lead.get_quotes().filter(id__in=quotes_ids)
            if not queryset.exists() or queryset.count() != len(quotes_ids):
                raise mixins.APIException(constants.INVALID_INPUT)
            return queryset
        except (KeyError, Lead.DoesNotExist):
            raise mixins.APIException(constants.LEAD_ERROR)
        except ValueError:
            raise mixins.APIException(constants.INVALID_INPUT)


class GetRecommendatedQuotes(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuoteRecommendationSerializer

    def get_queryset(self):
        try:
            lead = Lead.objects.get(id=self.request.query_params['lead'])
            with transaction.atomic():
                if self.request.query_params.get('suminsured'):
                    lead.final_score = self.request.query_params['suminsured']
                    lead.save()
                elif self.request.query_params.get('reset'):
                    lead.calculate_final_score()
                return lead.get_recommendated_quotes()
        except (KeyError, Lead.DoesNotExist):
            raise mixins.APIException(constants.LEAD_ERROR)
        except ValueError:
            raise mixins.APIException(constants.INVALID_INPUT)
        except IntegrityError:
            pass
        raise mixins.APIException(
            'Curently we are unable to suggest any quote. please try again.')
