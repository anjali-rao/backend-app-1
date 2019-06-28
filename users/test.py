# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.urls import include, path
from django.test import TestCase
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import URLPatternsTestCase, APITestCase

from users.models import User
from utils.test_utils import (
    add_data, generate_otp, otp_verification, register_user, login_user
)


class UserAPISTestCases(APITestCase, URLPatternsTestCase):
    """
    This Test related to testing Generate OTP apis
    and user registration
    """

    transaction_id = ''
    PHONE_NO = 6362843965
    PASSCODE = 4321
    urlpatterns = [
        path('', include('goplannr.apis_urls')),
    ]

    def test_generate_otp(self):
        generate_otp(self, self.PHONE_NO, status.HTTP_200_OK)

    def test_invalid_phone_no(self):
        generate_otp(self, 636284396, status.HTTP_400_BAD_REQUEST)

    def test_invalid_data(self):
        generate_otp(self, 'qwerty123', status.HTTP_400_BAD_REQUEST)

    def test_valid_otp_verification(self):
        otp = cache.get('OTP:' + str(self.PHONE_NO) + '')
        response = otp_verification(
            self=self,
            otp=otp,
            phone_no=self.PHONE_NO,
            status_code=status.HTTP_200_OK
        )

    def test_invalid_otp_verification(self):
        otp_verification(
            self=self,
            otp=12345,
            phone_no=self.PHONE_NO,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def test_otp_verification_invalid_phone_no(self):
        otp = cache.get('OTP:' + str(self.PHONE_NO) + '')
        otp_verification(
            self=self,
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


    def check_user_type(self, user_id, user_type):
        self.assertEqual(User.objects.get(id=user_id).user_type, user_type)

    def test_register_subscriber(self):
        add_data()
        user_id = register_user(self, self.PHONE_NO, 'OCOVR-2-4', self.PASSCODE)
        self.check_user_type(user_id, 'subscriber')

    def test_register_existing_user(self):
        add_data()
        user_id = register_user(self, self.PHONE_NO, 'OCOVR-2-4', self.PASSCODE)
        register_user(
            self=self,
            phone_no=self.PHONE_NO,
            promo_code='OCOVR-2-4',
            passcode=self.PASSCODE,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def test_register_transaction_user(self):
        add_data()
        user_id = register_user(self, 6362843967, "OCOVR-1-3", self.PASSCODE)
        self.check_user_type(user_id, "pos")

    def test_register_enterprise_user(self):
        add_data()
        user_id = register_user(self, 6362843968, 'HDFC-1-3', self.PASSCODE)
        self.check_user_type(user_id, 'enterprise')

    def change_password(
            self,
            phone_no,
            passcode,
            status_code=status.HTTP_200_OK):

        generate_otp(self, self.PHONE_NO, status.HTTP_200_OK)
        otp = cache.get('OTP:' + str(self.PHONE_NO) + '')
        response = otp_verification(
            self=self,
            otp=otp,
            phone_no=self.PHONE_NO,
            status_code=status.HTTP_200_OK
        )

        transaction_id = response.json().get('transaction_id', '')
        self.assertEqual(not transaction_id, False)
        data = dict(
            phone_no=self.PHONE_NO,
            new_password=str(self.PHONE_NO) + str(passcode),
            transaction_id=transaction_id
        )
        response = self.client.post('/v2/user/update/password', data)
        self.assertEqual(response.status_code, status_code)

    def test_change_password(self):
        passcode = 1234
        add_data()
        register_user(self, self.PHONE_NO, 'OCOVR-2-4', self.PASSCODE)
        self.change_password(self.PHONE_NO, passcode, status.HTTP_200_OK)
        login_user(self, self.PHONE_NO, passcode)

    def test_change_password_unregistered_phone_no(self):
        self.change_password(
            phone_no=1234567890,
            passcode=1234,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def test_login_registered_user(self):
        passcode = 1234
        add_data()
        register_user(
            self=self,
            phone_no=self.PHONE_NO,
            passcode=passcode,
            promo_code='OCOVR-2-4'
        )
        login_user(self, self.PHONE_NO, passcode)

    def test_login_unregistered_user(self):
        login_user(
            self=self,
            phone_no=1234567890,
            passcode=1111,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def update_user(
            self,
            pincode,
            first_name,
            auth_token,
            status_code=status.HTTP_200_OK):

        header = dict(
            HTTP_AUTHORIZATION=auth_token
        )
        data = dict(
            pincode=pincode,
            phone_no=self.PHONE_NO,
            first_name=first_name,
        )
        response = self.client.patch('/v1/user/update', data, **header)
        self.assertEqual(response.status_code, status_code)

    def test_update_user(self):
        passcode = 1234

        add_data()
        register_user(
            self=self,
            phone_no=self.PHONE_NO,
            passcode=passcode,
            promo_code='OCOVR-2-4'
        )

        response = login_user(self, self.PHONE_NO, passcode)
        auth_token = response.get('authorization')
        self.assertEqual(not auth_token, False)

        self.update_user(
            pincode=560011,
            first_name='updateuser',
            auth_token=auth_token
        )

    def test_update_user_invalid_data(self):
        pincode = 560111
        first_name = 'updateuser'
        passcode = 1234

        add_data()
        register_user(
            self=self,
            phone_no=self.PHONE_NO,
            passcode=passcode,
            promo_code='OCOVR-2-4'
        )

        response = login_user(self, self.PHONE_NO, passcode)
        auth_token = response.get('authorization')
        self.assertEqual(not auth_token, False)

        self.update_user(
            pincode=pincode,
            first_name=first_name,
            auth_token=auth_token,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def test_update_invalid_authtoken(self):
        self.update_user(
            pincode='560111',
            first_name='updateduser',
            auth_token='auth_token',
            status_code=status.HTTP_403_FORBIDDEN
        )

    def test_user_details(self):
        add_data()
        user_id = register_user(
            self=self,
            phone_no=self.PHONE_NO,
            passcode=self.PASSCODE,
            promo_code='OCOVR-2-4'
        )
        response =  login_user(self, self.PHONE_NO, self.PASSCODE)
        auth_token = response.get('authorization')
        self.assertEqual(not auth_token, False)
        header = dict(
            HTTP_AUTHORIZATION=auth_token
        )

        response = self.client.get('/v2/user/' + str(user_id) + '/details', **header)
        self.assertEqual(int(response.json().get('agent_id')), user_id)

    def test_invalid_user_details(self):
        add_data()
        user_id = register_user(
            self=self,
            phone_no=self.PHONE_NO,
            passcode=self.PASSCODE,
            promo_code='OCOVR-2-4'
        )
        response =  login_user(self, self.PHONE_NO, self.PASSCODE)
        auth_token = response.get('authorization')
        self.assertEqual(not auth_token, False)
        header = dict(
            HTTP_AUTHORIZATION=auth_token
        )

        response = self.client.get('/v2/user/12/details', **header)
        self.assertEqual(response.json().get('agent_id'), None)


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
