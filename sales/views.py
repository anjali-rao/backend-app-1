# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, status
from rest_framework.response import Response

from users.decorators import UserAuthentication
from utils import mixins, constants
from sales.serializers import (
    CreateApplicationSerializer, GetProposalDetailsSerializer,
    Application, UpdateContactDetailsSerializer, Contact,
    GetApplicationMembersSerializer, CreateMemberSerializers,
    CreateNomineeSerializer, MemberSerializer, HealthInsuranceSerializer,
    TravalInsuranceSerializer, TermsSerializer, ExistingPolicySerializer,
    GetInsuranceFieldsSerializer, ApplicationSummarySerializer
)

from django.core.exceptions import ValidationError
from django.http import Http404
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404 as _get_object_or_404


class CreateApplication(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CreateApplicationSerializer


class RetrieveUpdateProposerDetails(
        mixins.MethodSerializerView, generics.RetrieveUpdateAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = Application.objects.all()
    _obj = None

    method_serializer_classes = {
        ('GET', ): GetProposalDetailsSerializer,
        ('PATCH'): UpdateContactDetailsSerializer
    }

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (constants.LOOKUP_ERROR % (
            self.__class__.__name__, lookup_url_kwarg)
        )

        if 'search' in self.request.query_params and self.request.method == 'GET': # noqa
            self._obj = Contact.objects.filter(
                phone_no=self.request.query_params.get('search')
            ).order_by('modified').first()
        if not self._obj:
            filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
            try:
                application = _get_object_or_404(queryset, **filter_kwargs)
                self._obj = application.quote.lead.contact
            except (TypeError, ValueError, ValidationError):
                self._obj = Http404
        # May raise a permission denied
        self.check_object_permissions(self.request, self._obj)
        return self._obj

    def perform_update(self, serializer):
        serializer.save(
            application_id=self.kwargs['pk'],
            user_id=self.request.user.id)


class RetrieveUpdateApplicationMembers(
        mixins.MethodSerializerView, generics.ListCreateAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = Application.objects.all()
    method_serializer_classes = {
        ('GET', ): GetApplicationMembersSerializer,
        ('POST'): CreateMemberSerializers
    }

    def get(self, request, *args, **kwargs):
        members = self.get_object().member_set.all()
        members = sorted(
            members, key=lambda member: constants.MEMBER_ORDER.get(
                member.relation, 0))
        return Response(
            self.get_serializer(members, many=True).data,
            status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        try:
            with transaction.atomic():
                application.active_members.filter(
                    relation__in=['son', 'daughter']).update(ignore=True)
                application.active_members.exclude(
                    relation__in=['son', 'daughter']).update(ignore=None)
                for member in request.data:
                    serializer = self.get_serializer_class()(data=member)
                    serializer.is_valid(raise_exception=True)
                    serializer.save(application_id=application.id)
                from sales.tasks import update_insurance_fields
                # To Dos' Use Celery
                update_insurance_fields(application_id=application.id)
                getattr(
                    application, application.application_type).switch_premium(
                    application.adults, application.childrens)
                application.member_set.filter(ignore=None).update(ignore=True)
                application.refresh_from_db()
                application.update_fields(**dict(stage='nominee_details'))
        except (IntegrityError, mixins.RecommendationException) as e:
            raise mixins.APIException(e)
        return Response(dict(
            premium=application.quote.premium.amount,
            member=MemberSerializer(
                application.active_members, many=True).data),
            status=status.HTTP_201_CREATED)


class CreateApplicationNominee(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CreateNomineeSerializer
    queryset = Application.objects.all()

    def perform_create(self, serializer):
        with transaction.atomic():
            app = self.get_object()
            serializer.save(application_id=app.id)
            app.refresh_from_db()
            app.update_fields(**dict(stage='health_details'))


class CreateExistingPolicies(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = ExistingPolicySerializer
    queryset = Application.objects.all()

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save(application_id=self.get_object().id)


class UpdateInsuranceFields(generics.UpdateAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = Application.objects.all()
    insurance_serializer_classes = dict(
        healthinsurance=HealthInsuranceSerializer,
        travelinsurance=TravalInsuranceSerializer
    )
    application_type = None

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (constants.LOOKUP_ERROR % (
            self.__class__.__name__, lookup_url_kwarg)
        )
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        try:
            self.application = _get_object_or_404(queryset, **filter_kwargs)
            self.application_type = self.application.application_type
            if not hasattr(
                    self.application, self.application.application_type):
                self._obj = Http404
            else:
                self._obj = getattr(
                    self.application, self.application.application_type)
        except (TypeError, ValueError, ValidationError):
            self._obj = Http404
        # May raise a permission denied
        self.check_object_permissions(self.request, self._obj)
        return self._obj

    def get_serializer_class(self):
        serializer_cls = self.insurance_serializer_classes.get(
            self.application_type)
        if serializer_cls:
            return serializer_cls

        raise mixins.APIException(constants.APPLICATION_UNMAPPED)

    def perform_update(self, serializer):
        with transaction.atomic():
            serializer.save()
            self.application.stage = 'summary'
            self.application.save()


class GetInsuranceFields(generics.RetrieveAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = Application.objects.all()
    serializer_class = GetInsuranceFieldsSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not hasattr(instance, instance.application_type):
            raise mixins.APIException(constants.APPLICATION_UNMAPPED)
        insurance = getattr(instance, instance.application_type)
        data = list()
        members = MemberSerializer(instance.active_members, many=True).data
        for field in insurance._meta.fields:
            if field.name in constants.INSURANCE_EXCLUDE_FIELDS:
                continue
            serializer = self.get_serializer(data=dict(
                text=field.help_text,
                field_name=field.name,
                field_requirements=[{
                    'relation': "None"
                }] if field.__class__.__name__ in [
                    'BooleanField', 'IntegerField'] else members
            ))
            serializer.is_valid(raise_exception=True)
            data.append(serializer.data)
        return Response(data)


class ApplicationSummary(generics.RetrieveUpdateAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = Application.objects.all()
    serializer_class = ApplicationSummarySerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        nominee = instance.nominee_set.first()
        if not nominee:
            raise mixins.APIException(
                constants.INCOMPLETE_APPLICATION % 'nominee details')
        if not hasattr(instance, instance.application_type):
            raise mixins.APIException(constants.APPLICATION_UNMAPPED)

        serializer = self.get_serializer(instance)
        data = serializer.data

        data['%s_fields' % (
            instance.application_type)] = getattr(
                instance, instance.application_type).get_summary()
        return Response(data)


class SubmitApplication(generics.UpdateAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = Application.objects.all()
    serializer_class = TermsSerializer

    def perform_update(self, serializer):
        with transaction.atomic():
            serializer.save()
            application = self.get_object()
            application.refresh_from_db()
            application.stage = 'completed'
            application.save()
