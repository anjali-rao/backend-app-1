# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, exceptions

from users.decorators import UserAuthentication
from sales.serializers import (
    CreateApplicationSerializer
)


class CreateApplication(generics.CreateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CreateApplicationSerializer
