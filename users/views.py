# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from crm.serializers import LeadSerializer
from sales.serializers import ClientSerializer
from users.serializers import (
    CreateUserSerializer, OTPGenrationSerializer, OTPVerificationSerializer,
    AuthorizationSerializer, ChangePasswordSerializer,
    AccountSearchSerializers, User, PincodeSerializer, Pincode,
    UpdateUserSerializer, UserEarningSerializer, UserDetailSerializer
)
from sales.serializers import SalesApplicationSerializer
from users.decorators import UserAuthentication
from utils import constants
from utils.mixins import APIException
from content.serializers import (
    EnterprisePlaylistSerializer, AppoinmentSerializer, Appointment)

from django.db.models import Q
from django.db import transaction, IntegrityError


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
                    raise APIException(constants.PASSWORD_REQUIRED)
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
        except IntegrityError as e:
            raise APIException(constants.USER_ALREADY_EXISTS)

        return Response(serializer.response, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def generate_authorization(request, version):
    serializer = AuthorizationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(
        serializer.response, status=status.HTTP_200_OK)


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


class GetCart(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = SalesApplicationSerializer

    def get_queryset(self):
        return self.request.user.get_applications(
            status=['pending', 'fresh', 'submitted'])


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
                if data['playlist_type'] in constants.PLAYLIST_CHOICES:
                    return playlists.filter(
                        playlist__playlist_type=data['playlist_type'])
                raise APIException(constants.INVALID_PLAYLIST_TYPE)
            return playlists
        raise APIException(constants.PLAYLIST_UNAVAILABLE)


class UpdateUser(generics.UpdateAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = UpdateUserSerializer

    def get_object(self):
        return self.request.user


class GetUserDetails(generics.RetrieveAPIView):
    serializer_class = UserDetailSerializer
    queryset = User.objects.all()


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
