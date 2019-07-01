# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from users.serializers import (
    CreateUserSerializer, OTPGenrationSerializer, OTPVerificationSerializer,
    AuthorizationSerializer, ChangePasswordSerializer,
    AccountSearchSerializers, User, PincodeSerializer, Pincode,
    UpdateUserSerializer, UserEarningSerializer, UserDetailSerializerV2,
    UserDetailSerializerV3, LeadSerializer, ContactSerializers,
    ClientSerializer, AdvisorSerializer, SendSMSSerializer
)
from sales.serializers import SalesApplicationSerializer
from users.decorators import UserAuthentication
from utils import constants as Constants
from utils.mixins import APIException
from content.serializers import (
    EnterprisePlaylistSerializer, AppoinmentSerializer, Appointment)

from django.db.models import Q
from django.db import transaction, IntegrityError
from django.core.cache import cache


@api_view(['POST'])
def generate_otp(request, version):
    serializer = OTPGenrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(
        serializer.response, status=status.HTTP_200_OK)


@api_view(['POST'])
def verify_otp(request, version):
    serializer = OTPVerificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(
        serializer.response, status=status.HTTP_200_OK)


class RegisterUser(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CreateUserSerializer

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                if 'manager_id' not in request.data and 'password' not in request.data:  # noqa
                    raise APIException(Constants.PASSWORD_REQUIRED)
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
        except IntegrityError:
            raise APIException(Constants.USER_ALREADY_EXISTS)
        return Response(serializer.response, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def generate_authorization(request, version):
    serializer = AuthorizationSerializer(data=request.data)
    if 'phone_no' in request.data:
        from users.models import Account
        acc = Account.objects.filter(phone_no=request.data['phone_no'])
        if not acc.exists():
            raise APIException(Constants.INVALID_PHONE_NO)
    serializer.is_valid(raise_exception=True)
    return Response(
        serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_password(request, version):
    # To Dos: Add Authentication
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(
        serializer.response, status=status.HTTP_200_OK)


class SearchAccount(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AccountSearchSerializers

    def get_queryset(self):

        query = {}
        filter_location = {}
        params = self.request.query_params

        filter_location[0] = 'account__address__pincode__state__name'
        filter_location[1] = 'account__address__pincode__city'
        filter_location[2] = 'account__address__pincode__pincode'

        query['user_type__in'] = ['subscriber']

        if params.get('location'):
            location_info = params.get('location', '').split(', ')

            for index, value in enumerate(location_info):
                query[filter_location.get(index)] = value

        if params.get('category'):
            query['subscriber_enterprise_user__categories__name'] = params.get(
                'category', '').title()

        try:
            return User.objects.filter(**query)
        except Exception:
            pass
        return []


class PincodeSearch(APIView):

    def get(self, request, version):

        data = []
        text = request.query_params.get('text')
        try:
            if text:
                text = str(text).title()
                pincodes = Pincode.objects.filter(
                    Q(pincode__contains=text) | Q(city__contains=text) |
                    Q(state__name__contains=text))[:50]
                if pincodes:
                    data = PincodeSerializer(pincodes, many=True).data
                    data = self.format_location_data(data, text)

                return Response(data, status=status.HTTP_200_OK)
            raise APIException('Please pass a text parameter.')
        except Exception as e:
            raise APIException(e)

    def format_location_data(self, data, text):
        location_list = set()

        for each_location in data:
            location_string_list = list()

            state = each_location.get('state', '')
            city = each_location.get('city', '')
            pincode = each_location.get('pincode', '')

            if text in state:
                location_string_list.append(state)

            if text in city:
                location_string_list.append(state)
                location_string_list.append(city)

            if text in pincode:
                location_string_list.append(state)
                location_string_list.append(city)
                location_string_list.append(pincode)

            location_string_list = self.remove_duplicates(location_string_list)

            location_item = ', '.join(location_string_list)
            location_list.add(location_item)

        return location_list

    @staticmethod
    def remove_duplicates(location_string_list):
        cleaned_list = []

        for loc in location_string_list:
            if loc not in cleaned_list:
                cleaned_list.append(loc)

        return cleaned_list


class GetEarnings(generics.RetrieveAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = User.objects.all()
    serializer_class = UserEarningSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        cached_response = cache.get('USER_EARNINGS:%s' % self.request.user.id)
        if cached_response is not None:
            return Response(cached_response)
        self.object = self.get_object()
        serializer = self.get_serializer(self.object)
        response = serializer.data
        cache.set(
            'USER_EARNINGS:%s' % self.request.user.id, response,
            Constants.API_TTL)
        return Response(serializer.data)


class GetCart(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = SalesApplicationSerializer

    def get_queryset(self):
        cached_queryset = cache.get('USER_CART:%s' % self.request.user.id)
        if cached_queryset is not None:
            return cached_queryset
        queryset = self.request.user.get_applications(status=[
            'pending', 'fresh', 'submitted', 'approved', 'payment_due'])
        cache.set(
            'USER_CART:%s' % self.request.user.id, queryset, Constants.API_TTL)
        return queryset


class GetLeads(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = LeadSerializer

    def get_queryset(self):
        from crm.models import Lead
        return Lead.objects.filter(
            user_id=self.request.user.id, ignore=False).exclude(contact=None)


class GetClients(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = ClientSerializer

    def get_queryset(self):
        return self.request.user.get_applications(status=[
            'submitted', 'approved', 'completed'])


class GetContact(generics.RetrieveAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = ContactSerializers

    def retrieve(self, request, version, *args, **kwargs):
        self.object = self.request.user
        cache_response = cache.get('USER_CONTACTS:%s' % self.object.id)
        if cache_response:
            return Response(cache_response)
        serializer = self.get_serializer(self.object)
        response = serializer.data
        cache.set(
            'USER_CONTACTS:%s' % self.object.id, response,
            Constants.API_TTL)
        return Response(serializer.data)


class GetPlaylist(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = EnterprisePlaylistSerializer

    def get_queryset(self):
        enterprise = self.request.user.enterprise
        data = self.request.query_params
        playlists = enterprise.enterpriseplaylist_set.select_related(
            'playlist')
        if playlists.exists():
            if 'playlist_type' in data:
                if data['playlist_type'] in Constants.PLAYLIST_CHOICES:
                    return playlists.filter(
                        playlist__playlist_type=data['playlist_type'])
                raise APIException(Constants.INVALID_PLAYLIST_TYPE)
            return playlists
        raise APIException(Constants.PLAYLIST_UNAVAILABLE)


class UpdateUser(generics.UpdateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = UpdateUserSerializer

    def get_object(self):
        return self.request.user


class GetUserDetails(generics.RetrieveAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = User.objects.all()
    version_serializer = dict(
        v2=UserDetailSerializerV2, v3=UserDetailSerializerV3)

    def get_serializer_class(self):
        return self.version_serializer.get(
            self.kwargs['version'], UserDetailSerializerV2)

    def retrieve(self, request, *args, **kwargs):
        cache_response = cache.get('USER_DETAIL:%s' % kwargs.get('pk', ''))
        if cache_response:
            return Response(cache_response)
        self.object = self.get_object()
        serializer = self.get_serializer(self.object)
        response = serializer.data
        cache.set(
            'USER_DETAIL:%s' % kwargs.get('pk', ''), response,
            Constants.API_TTL)
        return Response(serializer.data)


class CreateAppointment(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = AppoinmentSerializer

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            data = request.data
            if self.request.user.id:
                data['user'] = self.request.user.id
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            if Appointment.objects.filter(
                user_id=data['user'], date=data['date'],
                    phone_no=data['phone_no']).exists():
                raise APIException('Appointment already scheduled.')
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AdvisorProfile(generics.RetrieveAPIView):
    permissions = [permissions.AllowAny]
    serializer_class = AdvisorSerializer
    queryset = User.objects.all()
    lookup_field = 'account__username'


@api_view(['POST'])
def send_sms(request, version):
    serializer = SendSMSSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.send_sms()
    return Response(serializer.data, status=status.HTTP_200_OK)
