from __future__ import unicode_literals
from rest_framework import views, permissions, status, generics
from rest_framework.response import Response

from utils import constants
from users.serializers import CreateUserSerializer, UserSerializer


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
