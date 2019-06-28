# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
from django.urls import include, path

from rest_framework.test import URLPatternsTestCase, APITestCase
from utils.test_utils import (
    add_data, register_user, login_user
)

class SalesJourneyTestCases(APITestCase, URLPatternsTestCase):
    """
    Tests sales journey apis including questionnaires, answers,
    leads and quotes
    """
    urlpatterns = [
        path('', include('goplannr.apis_urls')),
    ]

    def test_get_questionnaire(self):
        add_data()
        register_user(self)
        #login_user(self)
