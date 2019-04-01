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
    AccountSearchSerializers, Account, PincodeSerializer, Pincode
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
        queryset = Account.objects.filter(
            user__user_type__in=['subscriber', 'pos'])
        params = self.request.query_params
        if 'pincode' in params:
            queryset = queryset.filter(pincode=params['pincode'])
        if 'company' in params:
            queryset = queryset.filter(
                user__enterprise__company_id=params['company'])
        if 'category' in params:
                queryset = queryset.filter(
                    user__enterprise__categories=params['category'])
        return queryset


class PincodeSearch(APIView):

    def get(self, request, version, format=None):

        data = []
        EMPTY_RESPONSE = {'message': 'Please pass a text parameter.'}
        status_code = status.HTTP_400_BAD_REQUEST
        text = request.query_params.get('text')

        try:

            if text:

                text = str(text).title()
                res = Pincode.objects.filter(
                    Q(pincode__contains=text) | Q(city__contains=text) |
                    Q(state__name__contains=text))[:10]

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

            location_string_list = []

            state = each_location.get('state') or ''
            city = each_location.get('city') or ''
            pincode = each_location.get('pincode') or ''

            if text in state:
                location_string_list.append(state)

            if text in city:
                location_string_list.append(state)
                location_string_list.append(city)

            else:
                location_string_list.append(state)
                location_string_list.append(city)
                location_string_list.append(pincode)

            location_item = ', '.join(location_string_list)
            location_list.add(location_item)


        return location_list
