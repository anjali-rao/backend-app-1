# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import include, path
from django.test import TestCase
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import URLPatternsTestCase, APITestCase

class UserAPISTestCases(APITestCase, URLPatternsTestCase):
    """
    This Test related to testing Generate OTP apis
    """

    PHONE_NO = 6362843965
    urlpatterns = [
        path('', include('goplannr.apis_urls')),
    ]

    def test_generate_otp(self):
        data = dict(phone_no=self.PHONE_NO)
        response = self.client.post('/v2/user/otp/generate', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_phone_no(self):
        data = dict(phone_no=636284396)
        response = self.client.post('/v2/user/otp/generate', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_data(self):
        data = dict(phone_no='qwerty123')
        response = self.client.post('/v2/user/otp/generate', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def otp_verification(self, otp, phone_no, status_code):
        data = dict(otp=otp, phone_no=phone_no)
        response = self.client.post('/v2/user/otp/verify', data)
        self.assertEqual(response.status_code, status_code)

    def test_valid_otp_verification(self):
        otp = cache.get('OTP:' + str(self.PHONE_NO) + '')
        self.otp_verification(
            otp=otp,
            phone_no=self.PHONE_NO,
            status_code=status.HTTP_200_OK
        )

    def test_invalid_otp_verification(self):
        self.otp_verification(
            otp=12345,
            phone_no=self.PHONE_NO,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def test_otp_verification_invalid_phone_no(self):
        otp = cache.get('OTP:' + str(self.PHONE_NO) + '')
        self.otp_verification(
            otp=otp,
            phone_no=1234567890,
            status_code=status.HTTP_400_BAD_REQUEST
        )

class PostmanAPITestCase(TestCase):

    def test_apis(self):
        import requests
        url = "https://oc-api-testing.herokuapp.com/api"
        payload = "------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name=\"url\"\r\n\r\nhttps://www.getpostman.com/collections/da05fb67a5583530d024\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--" # noqa
        headers = {
            'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW", # noqa
            'cache-control': "no-cache",
            'Postman-Token': "cbe1a49a-eb41-4a87-add8-91a52b8cc758"
        }
        #response = requests.post(url, data=payload, headers=headers)
        #self.assertNotIn(response.status_code, range(500, 600))
        #for row in response.json():
        #    self.assertNotIn(
        #        int(row['response']['status_code']), range(500, 600))
