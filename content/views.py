# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import generics, permissions
from rest_framework.filters import SearchFilter, OrderingFilter

from users.decorators import UserAuthentication
from utils.mixins import CustomPagination
from utils.constants import API_CACHE_TIME

from content.serializers import (
    Faq, FaqSerializer, ContactUsSerializer, NewsLetterSerializer,
    PromoBookSerializer, NetworkHospital, NetworkCoverageSerializer,
    ProductVariantHelpFileSerializer, ProductVariant,
    CompanyHelpLineSerializer, Company
)


class GetFaq(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['question', 'answer']

    @method_decorator(cache_page(API_CACHE_TIME))
    def dispatch(self, *args, **kwargs):
        return super(self.__class__, self).dispatch(*args, **kwargs)


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

    @method_decorator(cache_page(API_CACHE_TIME))
    def dispatch(self, *args, **kwargs):
        return super(self.__class__, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        from product.models import Company
        return NetworkHospital.objects.select_related(
            'company', 'pincode').filter(
                company_id__in=Company.objects.values_list('id', flat=True))


class GetHelpFiles(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = ProductVariantHelpFileSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        'product_variant__company_category__company__name',
        'product_variant__company_category__category__name']
    queryset = ProductVariant.objects.all()

    @method_decorator(cache_page(API_CACHE_TIME))
    def dispatch(self, *args, **kwargs):
        return super(GetHelpLines, self).dispatch(*args, **kwargs)


class GetHelpLines(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = CompanyHelpLineSerializer

    @method_decorator(cache_page(API_CACHE_TIME))
    def dispatch(self, *args, **kwargs):
        return super(self.__class__, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Company.objects.exclude(helpline=None)
