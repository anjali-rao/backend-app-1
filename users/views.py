from __future__ import unicode_literals
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view

from users.serializers import (
    CreateUserSerializer, UserSerializer,
    OTPGenrationSerializer, OTPVerificationSerializer,
    AuthorizationSerializer, ChangePasswordSerializer,
    UserSettings
)

from users.decorators import UserAuthentication


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
    read_serializer_class = UserSerializer
    action = None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.action = True
        return Response(
            self.get_serializer(serializer.get_user()).data,
            status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.action:
            return self.read_serializer_class
        return super(RegisterUser, self).get_serializer_class()


@api_view(['POST'])
def generate_authorization(request, version):
    serializer = AuthorizationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(
        serializer.response, status=status.HTTP_200_OK)


@api_view(['POST'])
def change_password(request, version):
    serializer = ChangePasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(
        serializer.response, status=status.HTTP_205_RESET_CONTENT)


class GetUserSettings(generics.ListAPIView):
    authentication_classes = (UserAuthentication, )
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSettings

    def get_queryset(self):
        from users.models import User
        return User.objects.get(id=self.request.user.id)

    def list(self, request, version):
        queryset = self.get_queryset()
        serializer = self.get_serializer_class()(queryset)
        return Response(serializer.data)
