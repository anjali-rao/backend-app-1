# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from rest_framework import permissions, status, generics, views
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes

from users.decorators import UserAuthentication

from product.serializers import (
	CompanyNameSerializers, CategoryNameSerializers,
	Company, Category
)


@api_view(['GET'])
@authentication_classes([UserAuthentication])
def get_user_categories(request, version):
    return Response(request.user.get_categories(), status=status.HTTP_200_OK)


class GetSearchParamater(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, version):
        return Response([
            {
                'company': CompanyNameSerializers(
                    Company.objects.all(), many=True).data,
                'category': CategoryNameSerializers(
                    Category.objects.all(), many=True).data
            }
        ])