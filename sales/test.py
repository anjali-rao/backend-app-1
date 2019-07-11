# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from urllib.parse import urlencode
import json

from django.core.cache import cache

from rest_framework import status

from utils.test_utils import BaseTestCase
from product.models import ProductVariant


class ApplicationTestCases(BaseTestCase):
    def setUp(self):
        super().setUp()

        # User authentication
        self.user_id = self.register_user().json().get('user_id')
        auth_token = self.login_user().json().get('authorization', '')
        self.header = dict(
            HTTP_AUTHORIZATION=auth_token
        )

        # Generating quotes
        self.answers = [
            {"answer_id": 2, "question_id": 1},
            {"answer_id": 8, "question_id": 2},
            {"answer_id": 13, "question_id": 3},
            {"answer_id": 17, "question_id": 4},
            {"answer_id": 22, "question_id": 5},
            {"answer_id": 27, "question_id": 6},
            {"answer_id": 10, "question_id": 7},
            {"answer_id": 42, "question_id": 8}
        ]
        self.add_questions_answers()
        self.response = self.create_lead(self.user_id, self.header).json()
        self.quotes = self.submit_answers(
            self.answers,
            opportunity_id=self.response.get('opportunity_id')
        ).json()

        for q in self.quotes:
            if q['product']['company'] == 'Aditya Birla Health Insurance':
                quote_id = q.get('quote_id')
                break

        self.application_data = dict(
            quote_id=quote_id,
            contact_no=1234567890,
            contact_name='test user'
        )

        self.member_data = [dict(
            gender='male',
            first_name='member',
            last_name='user',
            dob='2000-11-11',
            occupation='others',
            relation='self',
            height_inches='6',
            height_foot='6',
            weight='80'
        ), dict(
            gender='female',
            first_name='member2',
            last_name='user',
            dob='2001-11-11',
            occupation='others',
            relation='mother',
            height_inches='6',
            height_foot='6',
            weight='80'
        )]

        self.nominee_data = dict(
            first_name='nominee',
            last_name='user',
            phone_no='1324567890',
            relation='brother'
        )

    def get_insurance_fields(self, member):

        insurance_fields = {
            "gastrointestinal_disease": [
                {
                    "id": member,
                    "value": True
                }
            ],
            "neuronal_diseases": [
                {
                    "id": member,
                    "value": False
                }
            ],
            "respiratory_diseases": [
                {
                    "id": member,
                    "value": False
                }
            ],
            "cardiovascular_disease": [
                {
                    "id": member,
                    "value": False
                }
            ],
            "ent_diseases": [
                {
                    "id": member,
                    "value": False
                }
            ],
            "blood_diseases": [
                {
                    "id": member,
                    "value": False
                }
            ],
            "oncology_disease": [
                {
                    "id": member,
                    "value": False
                }
            ],
            "alcohol_consumption": 40,
            "tabacco_consumption": 0.0,
            "cigarette_consumption": 0.0,
            "previous_claim": False,
            "proposal_terms": False
        }
        return insurance_fields

    def create_application(self, version, data):
        response = self.client.post(
            path='/' + version + '/application/create',
            data=data,
            **self.header
        )
        return response

    def test_create_application_v2(self):
        data = dict(
            quote_id=self.quotes[0].get('quote_id'),
            contact_no=1234567890,
            contact_name='test user'
        )
        response = self.create_application('v2', self.application_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(not response.json().get('application_id'), False)

    def test_create_application_v3(self):
        response = self.create_application('v3', self.application_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_application_v2_invalid_quote(self):
        data = dict(
            quote_id=1000,
            contact_no=1234567890,
            contact_name='test user'
        )

        response = self.create_application('v2', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_existing_policies(self):
        application_id = self.create_application(
            'v3', self.application_data).json().get('application_id')
        data = dict(
            insurer='Aditya Birla Group',
            suminsured=500000,
            deductible=400000
        )
        response = self.client.post(
            '/v2/application/'+ str(application_id) + '/policies',
            data=data,
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_existing_policies(self):
        application_id = self.create_application(
            'v3', self.application_data).json().get('application_id')
        data = dict(
            suminsured=500000,
        )
        response = self.client.post(
            '/v2/application/'+ str(application_id) + '/policies',
            data=data,
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def update_proposal(self, pincode=560034):

        application = self.create_application(
            'v3', self.application_data).json()
        data = dict(
            first_name='test',
            middle_name='',
            last_name='user',
            phone_no=1234567890,
            pincode=pincode,
            annual_income=123000,
            occupation='others',
            marital_status='single',
            email='test@test.com',
            dob='1900-11-11',
            document_type='aadhar_card',
            document_number='1qazxsw23',
            flat_no='103',
            street='streetname',
        )
        response = self.client.patch(
            '/v1/application/'
            + str(application.get('application_id')) + '/contact',
            data=data,
            **self.header
        )
        return application

    def test_get_proposer_details(self):
        application_id = self.update_proposal().get('application_id')
        response = self.client.get(
            '/v2/application/' + str(application_id) + '/contact',
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Checking for a proposer detail
        self.assertEqual(int(response.json().get('phone_no')), 1234567890)

    def test_get_invalid_proposer_details(self):
        response = self.client.get(
            '/v2/application/100/contact',
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def add_members(self, application_id, data):
        response = self.client.post(
            '/v2/application/' + str(application_id) + '/members',
            data=json.dumps(data),
            content_type='application/json',
            **self.header
        )
        return response

    def test_add_members(self):
        application_id = self.update_proposal().get('application_id')
        response = self.add_members(application_id, self.member_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.json().get('member')), 2)

    def test_update_members(self):
        application_id = self.update_proposal().get('application_id')
        response = self.add_members(application_id, self.member_data)
        data = [dict(
            last_name='newuser',
            relation='self',
            dob='2000-11-11',
            height_inches='6',
            height_foot='6',
            weight='80'
        )]
        response = self.add_members(application_id, data)
        self.assertEqual(response.json().get('member')[0].get('full_name'), 'member newuser')

    def test_add_members_invalid_application(self):
        data = [dict(
            gender='male',
            first_name='member',
            last_name='user',
            dob='2000-11-11',
            relation='self',
        )]

        response = self.add_members(application_id=100, data=data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_members_incomplete_data(self):
        application_id = self.update_proposal().get('application_id')
        data = [dict(
            gender='male',
            first_name='member',
            last_name='user',
            occupation='others',
            relation='self',
            height_inches='6',
            height_foot='6',
            weight='80'
        )]
        response = self.add_members(application_id, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_members(self):
        application_id = self.update_proposal().get('application_id')
        self.add_members(application_id, self.member_data)
        response = self.client.get(
            '/v2/application/' + str(application_id) + '/members', **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_get_members_invalid_application(self):
        response = self.client.get(
            '/v2/application/100/members', **self.header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def add_nominee(self, application_id, data):
        response = self.client.post(
            '/v2/application/' + str(application_id) + '/nominee',
            data=data,
            **self.header
        )
        return response

    def test_add_nominee(self):
        application_id = self.update_proposal().get('application_id')
        response = self.add_nominee(application_id, self.nominee_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_nominee_invalid_application(self):
        response = self.add_nominee(100, self.nominee_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_invalid_nominee(self):
        application_id = self.update_proposal().get('application_id')
        data = dict(
            first_name='test',
            phone_no='1234567890',
        )
        response = self.add_nominee(application_id, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def update_insurance_fields(self, application_id, member):
        data = self.get_insurance_fields(member)
        response = self.client.put(
            '/v2/application/' + str(application_id) + '/insurance/update',
            json.dumps(data),
            content_type='application/json',
            **self.header
        )
        return response

    def test_update_insurance_fields(self):
        application_id = self.update_proposal().get('application_id')
        members = self.add_members(application_id, self.member_data).json()
        response = self.update_insurance_fields(
            application_id,
            members.get('member')[0].get('id')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_insurance_fields_invalid_member(self):
        application_id = self.update_proposal().get('application_id')
        response = self.update_insurance_fields(
            application_id,
            member=100
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_insurance_fields(self):
        application_id = self.update_proposal().get('application_id')
        members = self.add_members(application_id, self.member_data).json()
        self.update_insurance_fields(
            application_id,
            member=members.get('member')[0].get('id')
        )
        self.update_insurance_fields(
            application_id,
            member=members.get('member')[1].get('id')
        )
        response = self.client.get(
            '/v2/application/' + str(application_id) + '/insurance/fields',
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_insurance_fields_invalid_application(self):
        response = self.client.get(
            '/v2/application/100/insurance/fields',
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_application_summary(self):
        application_id = self.update_proposal().get('application_id')
        members = self.add_members(application_id, self.member_data).json()
        self.update_insurance_fields(
            application_id,
            member=members.get('member')[0].get('id')
        )
        self.update_insurance_fields(
            application_id,
            member=members.get('member')[1].get('id')
        )

        response = self.client.get(
            '/v1/application/' + str(application_id) + '/summary',
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_application_summary(self):
        response = self.client.get(
            '/v1/application/100/summary',
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def fill_application(self):
        application_id = self.update_proposal().get('application_id')
        members = self.add_members(application_id, self.member_data).json()
        self.add_nominee(application_id, self.nominee_data)
        self.update_insurance_fields(
            application_id,
            member=members.get('member')[0].get('id')
        )
        self.update_insurance_fields(
            application_id,
            member=members.get('member')[1].get('id')
        )
        return application_id

    def test_submit_application(self):
        application_id = self.fill_application()
        data = dict(terms_and_conditions=True)
        response = self.client.put(
            '/v1/application/' + str(application_id) + '/submit',
            data,
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(not response.json().get('reference_no'), False)

    def test_submit_invalid_application(self):
        data = dict(terms_and_conditions=True)
        response = self.client.put(
            '/v1/application/100/submit',
            data,
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_false_application(self):
        application_id = self.fill_application()
        data = dict(terms_and_conditions=False)
        response = self.client.put(
            '/v1/application/' + str(application_id) + '/submit',
            data,
            **self.header
        )

        #TODO: Change status to 400 after False value of terms is handled
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def submit_application(self):
        application_id = self.fill_application()
        data = dict(terms_and_conditions=False)
        response = self.client.put(
            '/v2/application/' + str(application_id) + '/submit',
            data,
            **self.header
        )
        return response

    def test_get_user_cart(self):
        application = self.submit_application().json()
        response = self.client.get('/v2/user/cart', **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()[0].get('reference_no'), application.get('reference_no')
        )

    def test_offline_payment(self):
        application_id = self.fill_application()
        data = dict(terms_and_conditions=True)
        self.client.put(
            '/v1/application/' + str(application_id) + '/submit',
            data,
            **self.header
        )
        response = self.client.get(
            '/v2/application/' + str(application_id) + '/paymentlink',
            **self.header
        )
        self.assertEqual(response.json().get('success'), False)

    def verify_client(self):
        application_id = self.fill_application()
        data = dict(terms_and_conditions=True)
        reference_no = self.client.put(
            '/v3/application/' + str(application_id) + '/submit',
            data,
            **self.header
        ).json().get('reference_no')
        data = dict(otp=cache.get('APP-%s:' % reference_no))
        response = self.client.post(
            '/v2/application/' + str(application_id) + '/verify',
            data,
            **self.header
        )
        return response

    def test_update_application_status(self):
        response = self.verify_client()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_application_status_invalid_otp(self):
        data = dict(otp=00000)
        application_id = self.fill_application()
        response = self.client.post(
            '/v2/application/' + str(application_id) + '/verify',
            data,
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_contacts_leads(self):
        self.verify_client()
        response = self.client.get(
            '/v2/user/contacts', **self.header
        )
        self.assertEqual(len(response.json().get('leads')), 1)
