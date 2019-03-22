# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics

from users.decorators import UserAuthentication
from sales.serializers import QuoteSerializers, Quote


class GetQuotes(generics.ListAPIView):
    authentication_classes = (UserAuthentication,)
    serializer_class = QuoteSerializers

    def get_queryset(self):
        return Quote.objects.filter(
            lead_id=self.request.query_params.get('lead'))
