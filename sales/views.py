# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, status
from rest_framework.response import Response

from users.decorators import UserAuthentication
from utils import mixins
from sales.serializers import (
    CreateApplicationSerializer, GetProposalDetailsSerializer,
    Application, UpdateContactDetailsSerializer, Contact,
    GetApplicationMembersSerializer, CreateMemberSerializers,
    CreateNomineeSerializer, MemberSerializer
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

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        if 'search' in self.request.query_params and self.request.method == 'GET':
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
        serializer.save(application_id=self.kwargs['pk'])


class RetrieveUpdateApplicationMembers(
        mixins.MethodSerializerView, generics.ListCreateAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = Application.objects.all()
    method_serializer_classes = {
        ('GET', ): GetApplicationMembersSerializer,
        ('POST'): CreateMemberSerializers
    }

    def get(self, request, *args, **kwargs):
        members = self.get_object().member_set.filter(ignore=False)
        return Response(
            self.get_serializer(members, many=True).data,
            status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        application = self.get_object()
        try:
            with transaction.atomic():
                for member in request.data:
                    serializer = self.get_serializer_class()(data=member)
                    serializer.is_valid(raise_exception=True)
                    serializer.save(application_id=application.id)
        except (IntegrityError) as e:
            raise mixins.APIException(e)
        return Response(MemberSerializer(
            application.active_members, many=True).data,
            status=status.HTTP_201_CREATED)


class CreateApplicationNominee(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CreateNomineeSerializer
    queryset = Application.objects.all()

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save(application_id=self.get_object().id)
