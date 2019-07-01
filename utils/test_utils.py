
from __future__ import unicode_literals

from django.core.cache import cache
from django.urls import include, path

from rest_framework.test import URLPatternsTestCase, APITestCase

from users.models import State, Pincode, PromoCode, Enterprise
from content.models import Playlist


class BaseTestCase(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path('', include('goplannr.apis_urls')),
    ]
    transaction_id = ''
    PHONE_NO = 6362843965
    PASSCODE = 4321

    def setUp(self):
        self.add_data()

    def add_data(self):
        state = State.objects.create(name="Karnataka")
        Pincode.objects.create(pincode=560034, city='Bangalore', state=state)
        Pincode.objects.create(pincode=560011, city='Bangalore', state=state)

        PromoCode.objects.create(code='OCOVR-2-4')
        PromoCode.objects.create(code='OCOVR-1-3')

        enterprise_code = PromoCode.objects.create(code='HDFC-1-3')
        Enterprise.objects.create(
            name="hdfc", enterprise_type="enterprise",
            promocode=enterprise_code)

        Playlist.objects.create(
            name='Health Insurance Training',
            url='https://www.youtube.com/playlist?list=PLO72qwRGaNMxOxhIvu5cc5C89jMrE6QFN', # noqa
            playlist_type='training', id=1)
        Playlist.objects.create(
            name='Marketing',
            url='https://www.youtube.com/playlist?list=PLO72qwRGaNMxWeOuJPJPl0fQuFoUINbVn', # noqa
            playlist_type='marketing', id=2)

    def generate_otp(self, phone_no):
        data = dict(phone_no=phone_no)
        response = self.client.post('/v2/user/otp/generate', data)
        return response

    def otp_verification(self, otp, phone_no):
        data = dict(otp=otp, phone_no=phone_no)
        response = self.client.post('/v2/user/otp/verify', data)
        return response

    def register_user(
            self, phone_no=1234567890,
            promo_code='OCOVR-2-4', passcode=1234):

        self.generate_otp(phone_no)
        otp = cache.get('OTP:' + str(phone_no) + '')
        response = self.otp_verification(otp=otp, phone_no=phone_no)
        transaction_id = response.json().get('transaction_id', '')
        self.assertEqual(not transaction_id, False)

        data = dict(
            first_name='enterprise',
            last_name='user', phone_no=phone_no,
            password=str(phone_no) + str(passcode),
            email='enterprise@test.com',
            pan_no='APOPG3676B', pincode=560034,
            promo_code=promo_code, transaction_id=transaction_id)

        response = self.client.post('/v2/user/register', data)

        return response

    def login_user(
            self, phone_no=1234567890, passcode=1234):

        data = dict(
            phone_no=phone_no, password=str(phone_no) + str(passcode))
        response = self.client.post('/v2/user/authorization/generate', data)
        return response