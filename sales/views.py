# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, status, views
from rest_framework.response import Response

from users.decorators import UserAuthentication
from utils import mixins, constants
from sales.serializers import (
    CreateApplicationSerializer, GetProposalDetailsSerializer,
    Application, UpdateContactDetailsSerializer, Contact,
    GetApplicationMembersSerializer, CreateMemberSerializers,
    CreateNomineeSerializer, MemberSerializer, HealthInsuranceSerializer,
    TravalInsuranceSerializer, TermsSerializer, ExistingPolicySerializer,
    GetInsuranceFieldsSerializer, ApplicationSummarySerializer,
    UpdateApplicationSerializers, VerifyProposerPhonenoSerializer
)

from django.core.exceptions import ValidationError
from django.http import Http404
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404 as _get_object_or_404


class CreateApplication(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CreateApplicationSerializer

    def create(self, request, version, *args, **kwargs):
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = serializer.data
            if version == 'v3':
                instance = serializer.instance
                data.update(ApplicationSummarySerializer(instance).data)
                data['%s_fields' % (
                    instance.application_type
                )] = getattr(
                    instance, instance.application_type
                ).get_insurance_fields()
            return Response(data)


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

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        try:
            application = _get_object_or_404(queryset, **filter_kwargs)
            self._obj = application.client or application.quote.opportunity.lead.contact # noqa
        except (TypeError, ValueError, ValidationError):
            self._obj = Http404

        if 'search' in self.request.query_params and self.request.method == 'GET': # noqa
            contacts = Contact.objects.filter(
                phone_no=self.request.query_params.get('search')
            ).exclude(last_name='').order_by('modified', 'created')
            if not contacts.exists():
                raise mixins.NotFound('Application field not found.')
            if self._obj and contacts:
                if self._obj.id not in contacts:
                    self._obj = contacts.first()
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
        ('POST'): CreateMemberSerializers}

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
                update_insurance_fields.delay(application_id=application.id)
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
        return Response(insurance.get_insurance_fields())


class ApplicationSummary(generics.RetrieveUpdateAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = Application.objects.all()
    serializer_class = ApplicationSummarySerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

#        nominee = instance.nominee_set.first()
#        if not nominee:
#            raise mixins.APIException(
#                constants.INCOMPLETE_APPLICATION % 'nominee details')
        if not hasattr(instance, instance.application_type):
            raise mixins.APIException(constants.APPLICATION_UNMAPPED)

        serializer = self.get_serializer(instance)
        data = serializer.data
        insurance = getattr(instance, instance.application_type)

        data['%s_fields' % (
            instance.application_type)] = insurance.get_summary()
        return Response(data)


class SubmitApplication(generics.UpdateAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = Application.objects.all()
    serializer_class = TermsSerializer

    def update(self, request, version, *args, **kwargs):
        with transaction.atomic():
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        return Response(self.get_response(
            version, serializer))

    def get_response(self, version, serializer):
        response = serializer.data
        instance = serializer.instance
        instance.refresh_from_db()
        if version == 'v3':
            instance.send_propser_otp()
            from sales.tasks import aggregator_operation
            aggregator_operation.delay(instance)
            return response
        response = serializer.data
        instance.stage = 'payment_due'
        try:
            instance.aggregator_operation()
            response['payment_status'] = True
        except Exception:
            response['payment_status'] = False
        instance.save()
        return response


class GetApplicationPaymentLink(views.APIView):
    authentication_classes = (UserAuthentication,)

    def get(self, request, pk, version):
        data = dict(success=False)
        try:
            app = Application.objects.get(id=pk)
            if not app.application.payment_ready:
                app.application.insurer_operation()
            data.update(dict(
                success=True, payment_link=app.application.get_payment_link()))
            app.stage = 'payment_due'
            app.save()
        except (Application.DoesNotExist, Exception):
            data['message'] = 'Could not generate payment link. Please go with offline mode' # noqa
        return Response(data)


class UpdateApplicationStatus(generics.UpdateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = UpdateApplicationSerializers
    queryset = Application.objects.all()


class VerifyProposerPhoneno(views.APIView):
    authentication_classes = (UserAuthentication,)

    def post(self, request, pk, version):
        try:
            instance = Application.objects.get(id=pk)
            serializer = VerifyProposerPhonenoSerializer(
                instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(client_verified=True)
            response = serializer.data
            response['payment_status'] = instance.payment_mode != 'offline'
            return Response(serializer.data)
        except Application.DoesNotExist:
            raise mixins.APIException(constants.INVALID_APPLICATION_ID)
