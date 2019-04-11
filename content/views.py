# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, permissions

from users.decorators import UserAuthentication

from content.serializers import (
    Faq, FaqSerializer, ContactUsSerializer, NewsLetterSerializer)


class GetFaq(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer


class ContactUsAPI(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ContactUsSerializer


class AddNewsLetterSubscriber(generics.CreateAPIView):
    permissions = [permissions.AllowAny]
    serializer_class = NewsLetterSerializer
