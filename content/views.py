# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, permissions
from rest_framework.filters import SearchFilter, OrderingFilter


from users.decorators import UserAuthentication
from utils.mixins import CustomPagination

from content.serializers import (
    Faq, FaqSerializer, ContactUsSerializer, NewsLetterSerializer,
    PromoBookSerializer, NetworkHospital, NetworkCoverageSerializer,
    HelpFileSerializer, HelpFile
)


class GetFaq(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['question', 'answer']


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


class GetHelpFiles(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = HelpFileSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        'company_category__company__name',
        'company_category__category__name']
    queryset = HelpFile.objects.all()
