
from __future__ import unicode_literals
import json

from django.core.cache import cache
from django.urls import include, path
from django.core.management import call_command

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

    def loaddata(self, filepath):
        import sys
        from os import devnull
        stdout_backup, sys.stdout = sys.stdout, open(devnull, 'a')
        call_command('loaddata', filepath)
        sys.stdout = stdout_backup

    @classmethod
    def setUpTestData(self):
        state = State.objects.create(name="Karnataka")
        Pincode.objects.create(pincode=560034, city='Bangalore', state=state)
        Pincode.objects.create(pincode=560078, city='Bangalore', state=state)
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

        import sys
        from os import devnull
        stdout_backup, sys.stdout = sys.stdout, open(devnull, 'a')
        call_command('loaddata', 'utils/dump/product.json')
        sys.stdout = stdout_backup

    def add_questions_answers(self):
        self.loaddata('utils/dump/questions.json')
        self.loaddata('utils/dump/answers.json')

    def create_lead(self, user_id, header, category=1):
        data = dict(category_id=category,
            family=dict(self=32), pincode=560034, gender='male')
        response = self.client.post(
            path='/v2/lead/create',
            data=json.dumps(data),
            content_type='application/json',
            **header
        )
        return response

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

    def submit_answers(self, answers, opportunity_id):
        data = dict(
            opportunity_id=opportunity_id,
            answers=answers
        )
        response = self.client.post(
            path="/v2/user/questionnaire/record",
            data=json.dumps(data),
            content_type='application/json',
            **self.header
        )
        return response
