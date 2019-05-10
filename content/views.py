# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, permissions
from rest_framework.filters import SearchFilter, OrderingFilter


from users.decorators import UserAuthentication
from utils.mixins import CustomPagination

from content.serializers import (
    Faq, FaqSerializer, ContactUsSerializer, NewsLetterSerializer,
    PromoBookSerializer, NetworkHospital, NetworkCoverageSerializer
)


class GetFaq(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer


class ContactUsAPI(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ContactUsSerializer


class AddNewsLetterSubscriber(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = NewsLetterSerializer


class AddPromotion(generics.CreateAPIView):
    permissions = [permissions.AllowAny]
    serializer_class = PromoBookSerializer


class GetNetworkHospital(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = NetworkCoverageSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        'company__name', '=pincode__pincode', 'pincode__city',
        'pincode__state__name']
    pagination_class = CustomPagination

    def get_queryset(self):
        from product.models import Company
        return NetworkHospital.objects.select_related(
            'company', 'pincode').filter(
                company_id__in=Company.objects.values_list('id', flat=True))
