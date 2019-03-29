# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import permissions, status, views
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes

from users.decorators import UserAuthentication

from product.serializers import (
    CompanyNameSerializers, CategoryNameSerializers,
    Company, Category
)

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from utils.constants import API_CACHE_TIME


@api_view(['GET'])
@authentication_classes([UserAuthentication])
def get_user_categories(request, version):
    return Response(request.user.get_categories(), status=status.HTTP_200_OK)


class GetSearchParamater(views.APIView):
    permission_classes = [permissions.AllowAny]

    @method_decorator(cache_page(API_CACHE_TIME))
    def get(self, request, version):
        return Response([
            {
                'company': CompanyNameSerializers(
                    Company.objects.all(), many=True).data,
                'category': CategoryNameSerializers(
                    Category.objects.all(), many=True).data
            }
        ])
