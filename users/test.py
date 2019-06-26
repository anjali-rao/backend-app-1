# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import include, path
from django.test import TestCase
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import URLPatternsTestCase, APITestCase

from users.models import State, Pincode, PromoCode, User, Enterprise
from content.models import Playlist

class UserAPISTestCases(APITestCase, URLPatternsTestCase):
    """
    This Test related to testing Generate OTP apis
    and user registration
    """

    transaction_id = ''
    PHONE_NO = 6362843965
    urlpatterns = [
        path('', include('goplannr.apis_urls')),
    ]

    def add_data(self):
        state = State.objects.create(name="Karnataka")
        Pincode.objects.create(pincode=560034, city='Bangalore', state=state)
        PromoCode.objects.create(code='OCOVR-2-4')
        PromoCode.objects.create(code='OCOVR-1-3')

        enterprise_code = PromoCode.objects.create(code='HDFC-1-3')
        Enterprise.objects.create(
            name="hdfc",
            enterprise_type="enterprise",
            promocode=enterprise_code
        )

        Playlist.objects.create(
            name='Health Insurance Training',
            url='https://www.youtube.com/playlist?list=PLO72qwRGaNMxOxhIvu5cc5C89jMrE6QFN',
            playlist_type='training',
            id=1)
        Playlist.objects.create(
            name='Marketing',
            url='https://www.youtube.com/playlist?list=PLO72qwRGaNMxWeOuJPJPl0fQuFoUINbVn',
            playlist_type='marketing',
            id=2)

    def generate_otp(self, phone_no, status_code):
        data = dict(phone_no=phone_no)
        response = self.client.post('/v2/user/otp/generate', data)
        self.assertEqual(response.status_code, status_code)

    def test_generate_otp(self):
        self.generate_otp(self.PHONE_NO, status.HTTP_200_OK)

    def test_invalid_phone_no(self):
        self.generate_otp(636284396, status.HTTP_400_BAD_REQUEST)

    def test_invalid_data(self):
        self.generate_otp('qwerty123', status.HTTP_400_BAD_REQUEST)

    def otp_verification(self, otp, phone_no, status_code):
        data = dict(otp=otp, phone_no=phone_no)
        response = self.client.post('/v2/user/otp/verify', data)
        self.assertEqual(response.status_code, status_code)
        return response

    def test_valid_otp_verification(self):
        otp = cache.get('OTP:' + str(self.PHONE_NO) + '')
        response = self.otp_verification(
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

    def test_register_invalid_user(self):
        data = dict(
            first_name='test',
            last_name='user',
            phone_no='6362843965',
            password='password',
            email='test@test.com',
            pan_no='APOPG3676B',
            pincode=560034,
            promo_code='OCOVR-2-4'
        )

        response = self.client.post('/v2/user/register', data)

        '''
        returns the following response:
        'Invalid pincode provided & Transaction Id is required & Invalid prmo code provided'
        '''
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def register_user(self, phone_no, promo_code, status_code=status.HTTP_201_CREATED):
        self.generate_otp(phone_no, status.HTTP_200_OK)
        otp = cache.get('OTP:' + str(phone_no) + '')
        response = self.otp_verification(
            otp=otp,
            phone_no=phone_no,
            status_code=status.HTTP_200_OK
        )
        transaction_id = response.json().get('transaction_id', '')
        self.assertEqual(not transaction_id, False)

        data = dict(
            first_name="enterprise",
            last_name="user",
            phone_no=phone_no,
            password="password",
            email="enterprise@test.com",
            pan_no="APOPG3676B",
            pincode=560034,
            promo_code=promo_code,
            transaction_id=transaction_id
        )

        response = self.client.post('/v2/user/register', data)
        self.assertEqual(response.status_code, status_code)

        return response.json().get('user_id', '')

    def check_user_type(self, user_id, user_type):
        self.assertEqual(User.objects.get(id=user_id).user_type, user_type)

    def test_register_subscriber(self):
        self.add_data()
        user_id = self.register_user(self.PHONE_NO, "OCOVR-2-4")
        self.check_user_type(user_id, "subscriber")

    def test_register_existing_user(self):
        self.add_data()
        user_id = self.register_user(self.PHONE_NO, "OCOVR-2-4")
        self.register_user(self.PHONE_NO, "OCOVR-2-4", status.HTTP_400_BAD_REQUEST)

    def test_register_transaction_user(self):
        self.add_data()
        user_id = self.register_user(6362843967, "OCOVR-1-3")
        self.check_user_type(user_id, "pos")

    def test_register_enterprise_user(self):
        self.add_data()
        user_id = self.register_user(6362843968, "HDFC-1-3")
        self.check_user_type(user_id, "enterprise")


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
