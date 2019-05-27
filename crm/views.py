# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, status
from rest_framework.response import Response

from utils import mixins, constants

from users.decorators import UserAuthentication
from crm.serializers import (
    QuoteSerializer, QuoteDetailsSerializer, Quote,
    QuotesCompareSerializer, QuoteRecommendationSerializer,
    CreateUpdateLeadSerializer, LeadDetailSerializer, Lead,
    NotesSerializer
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
                category_lead = lead.category_lead
                category_lead.predicted_suminsured = self.request.query_params[
                    'suminsured']
                category_lead.save()
            lead.refresh_from_db()
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
                    lead.category_lead.update_fields(**dict(
                        predicted_suminsured=self.request.query_params[
                            'suminsured']))
                elif self.request.query_params.get('reset'):
                    lead.calculate_suminsured()
                lead.refresh_from_db()
                return lead.get_recommendated_quotes()
        except (KeyError, Lead.DoesNotExist):
            raise mixins.APIException(constants.LEAD_ERROR)
        except ValueError:
            raise mixins.APIException(constants.INVALID_INPUT)
        except IntegrityError:
            pass
        raise mixins.APIException(
            'Curently we are unable to suggest any quote. please try again.')


class GetLeadDetails(generics.RetrieveAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = LeadDetailSerializer
    queryset = Lead.objects.exclude(ignore=True)


class AddLeadNotes(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = NotesSerializer
    queryset = Lead.objects.all()

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                lead = self.get_object()
                data = self.request.data
                if isinstance(data, dict):
                    data = [data]
                for row in data:
                    serializer = self.get_serializer(data=row)
                    serializer.is_valid(raise_exception=True)
                    serializer.save(lead_id=lead.id)
            return Response(dict(
                message='Notes added successfully', lead_id=lead.id
            ), status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            pass
        raise mixins.APIException(
            'Unable to process request currently. Please try again')
