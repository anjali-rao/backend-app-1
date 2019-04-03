from __future__ import unicode_literals
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.views import APIView
from django.db.models import Q

from url_filter.integrations.drf import DjangoFilterBackend

from users.serializers import (
    CreateUserSerializer, OTPGenrationSerializer, OTPVerificationSerializer,
    AuthorizationSerializer, ChangePasswordSerializer,
    AccountSearchSerializers, Account, User, PincodeSerializer, Pincode,
    UserSerializer
)


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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.response, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def generate_authorization(request, version):
    serializer = AuthorizationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(
        serializer.response, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_password(request, version):
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

        filter_location[0] = 'account__pincode__state__name'
        filter_location[1] = 'account__pincode__city'
        filter_location[2] = 'account__pincode__pincode'

        query['user_type__in'] = ['subscriber']

        if params.get('location'):
            location_info = params.get('location', '').split(', ')

            for index, value in enumerate(location_info):
                query[filter_location.get(index)] = value

        if params.get('category'):
            query['subscriber_enterprise_user__categories__name'] = params.get(
                'category', '').title()

        try:
            result = User.objects.filter(**query)
        except Exception as e:
            result = []
        
        return result


class PincodeSearch(APIView):

    def get(self, request, version, format=None):

        data = []
        EMPTY_RESPONSE = {'detail': 'Please pass a text parameter.'}

        status_code = status.HTTP_400_BAD_REQUEST
        text = request.query_params.get('text')

        try:

            if text:

                text = str(text).title()
                res = Pincode.objects.filter(
                    Q(pincode__contains=text) | Q(city__contains=text) |
                    Q(state__name__contains=text))[:50]

                if res:
                    data = PincodeSerializer(res, many=True).data
                    data = self.format_location_data(data, text)

                return Response(data, status=status.HTTP_200_OK)

            else:
                return Response(EMPTY_RESPONSE, status=status_code)

        except Exception as e:
            ERROR_RESPONSE = {'message': e}
            return Response(ERROR_RESPONSE, status=status_code)

    def format_location_data(self, data, text):
        location_list = set()

        for each_location in data:
            location_string_list = list()

            state = each_location.get('state') or ''
            city = each_location.get('city') or ''
            pincode = each_location.get('pincode') or ''

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
