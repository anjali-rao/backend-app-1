from __future__ import unicode_literals
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view

from users.serializers import (
    CreateUserSerializer, UserSerializer,
    OTPGenrationSerializer, OTPVerificationSerializer,
    AuthorizationSerializer, ChangePasswordSerializer,
    ForgotPasswordOTPSerializer
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


@api_view(['POST'])
def forgot_password_otp(request, version):
    serializer = ForgotPasswordOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(
        serializer.response, status=status.HTTP_200_OK)
