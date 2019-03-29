from __future__ import unicode_literals
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view

from users.serializers import (
    CreateUserSerializer, OTPGenrationSerializer, OTPVerificationSerializer,
    AuthorizationSerializer, ChangePasswordSerializer,
    AccountSearchSerializers, Account
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
