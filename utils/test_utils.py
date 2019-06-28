
from __future__ import unicode_literals, absolute_import
from django.core.cache import cache

from rest_framework import status

from users.models import State, Pincode, PromoCode, User, Enterprise
from content.models import Playlist

def add_data():
    state = State.objects.create(name="Karnataka")
    Pincode.objects.create(pincode=560034, city='Bangalore', state=state)
    Pincode.objects.create(pincode=560011, city='Bangalore', state=state)

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

def otp_verification(self, otp, phone_no, status_code):
    data = dict(otp=otp, phone_no=phone_no)
    response = self.client.post('/v2/user/otp/verify', data)
    self.assertEqual(response.status_code, status_code)
    return response

def register_user(self,
        phone_no=1234567890,
        promo_code='OCOVR-2-4',
        passcode=1234,
        status_code=status.HTTP_201_CREATED):

    generate_otp(self, phone_no, status.HTTP_200_OK)
    otp = cache.get('OTP:' + str(phone_no) + '')
    response = otp_verification(
        self=self,
        otp=otp,
        phone_no=phone_no,
        status_code=status.HTTP_200_OK
    )
    transaction_id = response.json().get('transaction_id', '')
    self.assertEqual(not transaction_id, False)

    data = dict(
        first_name='enterprise',
        last_name='user',
        phone_no=phone_no,
        password=str(phone_no) + str(passcode),
        email='enterprise@test.com',
        pan_no='APOPG3676B',
        pincode=560034,
        promo_code=promo_code,
        transaction_id=transaction_id
    )

    response = self.client.post('/v2/user/register', data)
    self.assertEqual(response.status_code, status_code)

    return response.json().get('user_id', '')

def login_user(self,
        phone_no=1234567890,
        passcode=1234,
        status_code=status.HTTP_200_OK):

    data = dict(
        phone_no=phone_no,
        password=str(phone_no) + str(passcode)
    )
    response = self.client.post('/v2/user/authorization/generate', data)
    self.assertEqual(response.status_code, status_code)
    return response.json()
