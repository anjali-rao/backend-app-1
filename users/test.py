# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.core.cache import cache

from rest_framework import status

from users.models import User
from utils.test_utils import BaseTestCase


class UserAPISTestCases(BaseTestCase):
    """
    This Test related to testing Generate OTP apis
    and user registration
    """

    def test_generate_otp(self):
        self.generate_otp(self.PHONE_NO, status.HTTP_200_OK)

    def test_invalid_phone_no(self):
        self.generate_otp(636284396, status.HTTP_400_BAD_REQUEST)

    def test_invalid_data(self):
        self.generate_otp('qwerty123', status.HTTP_400_BAD_REQUEST)

    def test_valid_otp_verification(self):
        otp = cache.get('OTP:' + str(self.PHONE_NO) + '')
        self.otp_verification(
            otp=otp, phone_no=self.PHONE_NO,
            status_code=status.HTTP_200_OK)

    def test_invalid_otp_verification(self):
        self.otp_verification(
            otp=12345, phone_no=self.PHONE_NO,
            status_code=status.HTTP_400_BAD_REQUEST)

    def test_otp_verification_invalid_phone_no(self):
        otp = cache.get('OTP:' + str(self.PHONE_NO) + '')
        self.otp_verification(
            otp=otp, phone_no=1234567890,
            status_code=status.HTTP_400_BAD_REQUEST)

    def test_register_invalid_user(self):
        data = dict(
            first_name='test', last_name='user',
            phone_no='6362843965', password='password',
            email='test@test.com', pan_no='APOPG3676B',
            pincode=560034, promo_code='OCOVR-2-4')

        response = self.client.post('/v2/user/register', data)

        '''
        returns the following response:
        'Invalid pincode provided & Transaction Id is required & Invalid prmo code provided'
        '''
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def check_user_type(self, user_id, user_type):
        self.assertEqual(User.objects.get(id=user_id).user_type, user_type)

    def test_register_subscriber(self):
        user_id = self.register_user(self.PHONE_NO, 'OCOVR-2-4', self.PASSCODE)
        self.check_user_type(user_id, 'subscriber')

    def test_register_existing_user(self):
        self.register_user(
            self.PHONE_NO, 'OCOVR-2-4', self.PASSCODE)
        self.register_user(
            phone_no=self.PHONE_NO,
            promo_code='OCOVR-2-4', passcode=self.PASSCODE,
            status_code=status.HTTP_400_BAD_REQUEST)

    def test_register_transaction_user(self):
        user_id = self.register_user(
            6362843967, "OCOVR-1-3", self.PASSCODE)
        self.check_user_type(user_id, "pos")

    def test_register_enterprise_user(self):
        user_id = self.register_user(
            6362843968, 'HDFC-1-3', self.PASSCODE)
        self.check_user_type(user_id, 'enterprise')

    def change_password(
            self, phone_no, passcode,
            status_code=status.HTTP_200_OK):
        self.generate_otp(self.PHONE_NO, status.HTTP_200_OK)
        otp = cache.get('OTP:' + str(self.PHONE_NO) + '')
        response = self.otp_verification(
            otp=otp, phone_no=self.PHONE_NO,
            status_code=status.HTTP_200_OK)

        transaction_id = response.json().get('transaction_id', '')
        self.assertEqual(not transaction_id, False)
        data = dict(
            phone_no=self.PHONE_NO,
            new_password=str(self.PHONE_NO) + str(passcode),
            transaction_id=transaction_id)
        response = self.client.post('/v2/user/update/password', data)
        self.assertEqual(response.status_code, status_code)

    def test_change_password(self):
        passcode = 1234
        self.register_user(self.PHONE_NO, 'OCOVR-2-4', self.PASSCODE)
        self.change_password(self.PHONE_NO, passcode, status.HTTP_200_OK)
        self.login_user(self.PHONE_NO, passcode)

    def test_change_password_unregistered_phone_no(self):
        self.change_password(
            phone_no=1234567890,
            passcode=1234,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    def test_login_registered_user(self):
        passcode = 1234
        self.register_user(
            phone_no=self.PHONE_NO,
            passcode=passcode,
            promo_code='OCOVR-2-4'
        )
        self.login_user(self.PHONE_NO, passcode)

    def test_login_unregistered_user(self):
        self.login_user(
            phone_no=1234567890, passcode=1111,
            status_code=status.HTTP_400_BAD_REQUEST)

    def update_user(
        self, pincode, first_name, auth_token,
            status_code=status.HTTP_200_OK):

        header = dict(HTTP_AUTHORIZATION=auth_token)
        data = dict(
            pincode=pincode, phone_no=self.PHONE_NO,
            first_name=first_name)
        response = self.client.patch('/v1/user/update', data, **header)
        self.assertEqual(response.status_code, status_code)

    def test_update_user(self):
        passcode = 1234
        self.register_user(
            phone_no=self.PHONE_NO, passcode=passcode,
            promo_code='OCOVR-2-4')

        response = self.login_user(self.PHONE_NO, passcode)
        auth_token = response.get('authorization')
        self.assertEqual(not auth_token, False)

        self.update_user(
            pincode=560011, first_name='updateuser',
            auth_token=auth_token)

    def test_update_user_invalid_data(self):
        pincode = 560111
        first_name = 'updateuser'
        passcode = 1234

        self.register_user(
            phone_no=self.PHONE_NO,
            passcode=passcode, promo_code='OCOVR-2-4')

        response = self.login_user(self.PHONE_NO, passcode)
        auth_token = response.get('authorization')
        self.assertEqual(not auth_token, False)

        self.update_user(
            pincode=pincode, first_name=first_name,
            auth_token=auth_token,
            status_code=status.HTTP_400_BAD_REQUEST)

    def test_update_invalid_authtoken(self):
        self.update_user(
            pincode='560111', first_name='updateduser',
            auth_token='auth_token', status_code=status.HTTP_403_FORBIDDEN)

    def test_user_details(self):
        user_id = self.register_user(
            phone_no=self.PHONE_NO,
            passcode=self.PASSCODE,
            promo_code='OCOVR-2-4')
        response = self.login_user(self.PHONE_NO, self.PASSCODE)
        auth_token = response.get('authorization')
        self.assertEqual(not auth_token, False)
        header = dict(
            HTTP_AUTHORIZATION=auth_token
        )

        response = self.client.get('/v2/user/' + str(user_id) + '/details', **header)
        self.assertEqual(int(response.json().get('agent_id')), user_id)

    def test_invalid_user_details(self):
        user_id = self.register_user(
            phone_no=self.PHONE_NO,
            passcode=self.PASSCODE,
            promo_code='OCOVR-2-4'
        )
        response =  self.login_user(self.PHONE_NO, self.PASSCODE)
        auth_token = response.get('authorization')
        self.assertEqual(not auth_token, False)
        header = dict(
            HTTP_AUTHORIZATION=auth_token
        )

        response = self.client.get('/v2/user/12/details', **header)
        self.assertEqual(response.json().get('agent_id'), None)
