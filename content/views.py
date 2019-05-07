# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics, permissions


from content.serializers import (
    Faq, FaqSerializer, ContactUsSerializer, NewsLetterSerializer)


class GetFaq(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer


class ContactUsAPI(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ContactUsSerializer


class AddNewsLetterSubscriber(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = NewsLetterSerializer
