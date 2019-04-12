# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, status
from rest_framework.response import Response
# from rest_framework.views import APIView

from users.decorators import UserAuthentication
from sales.serializers import (
    CreateApplicationSerializer, GetContactDetailsSerializer,
    Application, UpdateContactDetailsSerializer, Contact
)

from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404 as _get_object_or_404


class CreateApplication(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CreateApplicationSerializer


class GetContactDetails(generics.RetrieveAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = GetContactDetailsSerializer
    queryset = Contact.objects.all()

    def get_object(self):
        """
        Returns the object the view is displaying.
        You may want to override this if you need to provide non-standard
        queryset lookups.  Eg if objects are referenced using multiple
        keyword arguments in the url conf.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        try:
            obj = _get_object_or_404(queryset, **filter_kwargs)
        except (TypeError, ValueError, ValidationError):
            obj = Http404

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj.quote.lead.contacts.get()


class UpdateContactDetails(generics.GenericAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = UpdateContactDetailsSerializer

    def post(self, request, version, format=None):
        serializer = self.get_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
