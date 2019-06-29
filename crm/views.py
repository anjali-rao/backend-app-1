# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, status
from rest_framework.response import Response

from utils import mixins, constants as Constants

from users.decorators import UserAuthentication
from crm.serializers import (
    QuoteSerializer, QuoteDetailsSerializer, Quote,
    QuotesCompareSerializer, QuoteRecommendationSerializer,
    UpdateLeadSerializer, LeadDetailSerializer, Lead,
    NotesSerializer, CreateLeadSerializer, Opportunity,
    SharedQuoteDetailsSerializer
)

from django.db import transaction, IntegrityError


class CreateLead(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CreateLeadSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save(user_id=self.request.user.id)


class UpdateLead(generics.UpdateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = UpdateLeadSerializer
    queryset = Lead.objects.all()

    def perform_update(self, serializer):
        with transaction.atomic():
            data = self.request.data
            if 'opportunity_id' not in data and 'category_id' not in data:
                raise mixins.APIException(
                    Constants.OPPORTUNITY_OR_OPPERATION_ID_REQUIRED)
            serializer.save(user_id=self.request.user.id)


class GetQuotes(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuoteSerializer

    def get_queryset(self):
        try:
            data = self.request.query_params
            lead = Lead.objects.get(id=data['lead'])
            opportunities = Opportunity.objects.filter(
                id=data.get('opportunity_id'))
            if 'suminsured' in data and not opportunities.exists():
                raise mixins.APIException(Constants.OPPORTUNITY_ID_REQUIRED)
            if opportunities.exists():
                opportunity = opportunities.get()
                if 'suminsured' in data:
                    category_oppor = opportunity.category_opportunity
                    category_oppor.predicted_suminsured = data['suminsured']
                    category_oppor.save()
                opportunity.refresh_from_db()
                queryset = opportunity.get_quotes()
            else:
                queryset = lead.get_quotes()
            if not queryset.exists():
                raise mixins.NotFound(Constants.NO_QUOTES_FOUND)
            return queryset
        except (KeyError, Lead.DoesNotExist):
            raise mixins.APIException(Constants.LEAD_ERROR)
        except ValueError:
            raise mixins.APIException(Constants.INVALID_INPUT)


class QuoteDetails(generics.RetrieveAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuoteDetailsSerializer
    queryset = Quote.objects.all()


class QuotesComparision(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuotesCompareSerializer

    def get_queryset(self):
        try:
            data = self.request.query_params
            opportunity = Opportunity.objects.get(id=data['opportunity_id'])
            if not self.request.query_params.get('quotes') or len(
                    self.request.query_params['quotes'].split(',')) < 2:
                raise mixins.NotAcceptable(Constants.COMPARISION_ERROR)
            quotes_ids = self.request.query_params['quotes'].split(',')
            queryset = opportunity.get_quotes().filter(id__in=quotes_ids)
            if not queryset.exists() or queryset.count() != len(quotes_ids):
                raise mixins.APIException(Constants.INVALID_INPUT)
            return queryset
        except (KeyError, Opportunity.DoesNotExist):
            raise mixins.APIException(Constants.OPPORTUNITY_ID_REQUIRED)
        except ValueError:
            raise mixins.APIException(Constants.INVALID_INPUT)


class GetRecommendatedQuotes(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuoteRecommendationSerializer

    def get_queryset(self):
        try:
            data = self.request.query_params
            Lead.objects.get(id=data['lead'])
            opportunities = Opportunity.objects.filter(
                id=data.get('opportunity_id'), lead_id=data['lead'])
            if not opportunities.exists():
                raise mixins.APIException(Constants.OPPORTUNITY_DOES_NOT_EXIST)
            with transaction.atomic():
                opportunity = opportunities.get()
                if data.get('suminsured'):
                    opportunity = opportunities.get()
                    opportunity.category_opportunity.update_fields(**dict(
                        predicted_suminsured=self.request.query_params[
                            'suminsured']))
                opportunity.refresh_from_db()
                return opportunity.get_recommendated_quotes()
        except (KeyError, Lead.DoesNotExist):
            raise mixins.APIException(Constants.LEAD_ERROR)
        except ValueError:
            raise mixins.APIException(Constants.INVALID_INPUT)
        except IntegrityError:
            pass
        raise mixins.APIException(
            'Curently we are unable to suggest any quote. please try again.')


class GetSharedQuoteDetails(generics.RetrieveAPIView):
    serializer_class = SharedQuoteDetailsSerializer
    queryset = Quote.objects.all()


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
