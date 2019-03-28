# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics

from users.decorators import UserAuthentication

from content.serializers import Faq, FaqSerializer


class GetFaq(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    queryset = Faq.objects.all()
    serializer_class = FaqSerializer
