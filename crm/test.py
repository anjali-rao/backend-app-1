# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from rest_framework import status

from utils.test_utils import BaseTestCase


class LeadTestCases(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user_id = self.register_user().json()['user_id']
        self.auth_token = self.login_user().json().get('authorization', '')
        self.header = dict(
            HTTP_AUTHORIZATION=self.auth_token
        )

    def test_create_lead(self):
        response = self.create_lead(self.user_id, self.header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_invalid_lead(self):
        response = self.create_lead(user_id=2, category=2, header=self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_lead(self):
        response = self.create_lead(self.user_id, self.header)
        lead_id = str(response.json()['lead_id'])

        data = dict(
            pincode=560011,
            opportunity_id=response.json()['opportunity_id'],
        )
        response = self.client.patch(
            '/v2/lead/' + lead_id + '/update', data, **self.header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_invalid_lead(self):
        data = dict(
            pincode=560011,
            opportunity_id=1
        )
        response = self.client.patch('/v2/lead/10/update', data, **self.header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_lead_invalid_pincode(self):
        response = self.create_lead(self.user_id, self.header)
        lead_id = str(response.json()['lead_id'])

        data = dict(
            pincode=555555,
            opportunity_id=response.json()['opportunity_id']
        )
        response = self.client.patch(
            '/v2/lead/' + lead_id + '/update', data, **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_lead_invalid_opportunity(self):
        response = self.create_lead(self.user_id, self.header)
        lead_id = str(response.json()['lead_id'])

        data = dict(
            pincode=560011,
            opportunity_id=10
        )
        response = self.client.patch(
            '/v2/lead/' + lead_id + '/update', data, **self.header)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_lead(self):
        response = self.create_lead(self.user_id, self.header)
        lead_id = str(response.json()['lead_id'])
        response = self.client.get(
            path='/v2/lead/' + str(lead_id),
            **self.header
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['lead_id'], int(lead_id))

    def test_get_invalid_lead(self):
        response = self.client.get(
            path='/v2/lead/1',
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_notes(self):
        response = self.create_lead(self.user_id, self.header)
        lead_id = str(response.json()['lead_id'])
        data = [
            dict(title='note1', text='notetext1'),
            dict(title='note2', text='notetext2'),
        ]
        response = self.client.post(
            path='/v2/lead/' + lead_id + '/notes/create',
            data=json.dumps(data),
            content_type='application/json',
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_notes_invalid_lead(self):
        data = [
            dict(title='note1', text='notetext1'),
            dict(title='note2', text='notetext2'),
        ]
        response = self.client.post(
            path='/v2/lead/1/notes/create',
            data=json.dumps(data),
            content_type='application/json',
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_single_note(self):
        response = self.create_lead(self.user_id, self.header)
        lead_id = str(response.json()['lead_id'])
        data = dict(title='note1', text='notetext1'),
        response = self.client.post(
            path='/v2/lead/' + lead_id + '/notes/create',
            data=json.dumps(data),
            content_type='application/json',
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
