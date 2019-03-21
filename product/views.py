# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes

from users.decorators import UserAuthentication


@api_view(['GET'])
@authentication_classes([UserAuthentication])
def get_user_categories(request, version):
    return Response(request.user.get_categories(), status=status.HTTP_200_OK)
