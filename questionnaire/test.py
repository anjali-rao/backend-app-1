# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from urllib.parse import urlencode

from rest_framework import status

from utils.test_utils import BaseTestCase


class QuestionnaireTestCases(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user_id = self.register_user().json()['user_id']
        auth_token = self.login_user().json().get('authorization', '')
        self.header = dict(
            HTTP_AUTHORIZATION=auth_token
        )

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

    def test_get_questionnaire(self):
        self.add_questions_answers()
        params = dict(category=1)
        response = self.client.get(
            '/v2/user/questionnaire?'
            + urlencode(params),
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0].get('question_id'), 1)

    def test_get_invalid_questionnaire(self):
        params = dict(category=1)
        response = self.client.get(
            '/v2/user/questionnaire?'
            + urlencode(params),
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_answer(self):
        self.add_questions_answers()
        response = self.create_lead(self.user_id, self.header)

        response = self.submit_answers(
            self.answers, response.json().get('opportunity_id'))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreater(len(response.json()), 0)

    def test_submit_invalid_answer(self):
        response = self.create_lead(self.user_id, self.header)
        response = self.submit_answers(
            self.answers, response.json().get('opportunity_id'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_answer_invalid_lead(self):
        response = self.submit_answers(self.answers, opportunity_id=1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def get_quotes(self, data):
        response = self.client.get(
            '/v2/quotes?' + urlencode(data),
            content_type='application/json',
            **self.header
        )
        return response

    def test_get_lead_quotes(self):
        self.add_questions_answers()
        response = self.create_lead(self.user_id, self.header).json()
        self.submit_answers(
            self.answers,
            opportunity_id=response.get('opportunity_id')
        ).json()

        data = dict(lead=response['lead_id'])
        response = self.get_quotes(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.json()), 0)

    def test_get_invalid_lead_quotes(self):
        data = dict(lead=1)
        response = self.get_quotes(data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_opportunity_quotes(self):
        self.add_questions_answers()
        response = self.create_lead(self.user_id, self.header).json()
        self.submit_answers(
            self.answers,
            opportunity_id=response.get('opportunity_id')
        ).json()

        data = dict(
            lead=response.get('lead_id'),
            opportunity_id=response.get('opportunity_id')
        )
        response = self.get_quotes(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.json()), 0)

    def test_get_suminsured_quotes(self):
        self.add_questions_answers()
        response = self.create_lead(self.user_id, self.header).json()
        self.submit_answers(
            self.answers,
            opportunity_id=response.get('opportunity_id')
        ).json()

        data = dict(
            lead=response.get('lead_id'),
            opportunity_id=response.get('opportunity_id'),
            suminsured=500000
        )
        response = self.get_quotes(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0].get('sum_insured'), 500000)

    def test_quote_details(self):
        self.add_questions_answers()
        response = self.create_lead(self.user_id, self.header).json()
        quotes = self.submit_answers(
            self.answers,
            opportunity_id=response.get('opportunity_id')
        ).json()
        response = self.client.get(
            '/v2/quote/' + str(quotes[0].get('quote_id')),
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.json().keys()), 1)

    def test_invalid_quote_details(self):
        response = self.client.get(
            '/v2/quote/1',
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_compare_quotes(self):
        self.add_questions_answers()
        response = self.create_lead(self.user_id, self.header).json()
        quotes = self.submit_answers(
            self.answers,
            opportunity_id=response.get('opportunity_id')
        ).json()
        quote1 = quotes[0].get('quote_id')
        quote2 = quotes[1].get('quote_id')
        data = dict(
            quotes=str(quote1) + "," + str(quote2),
            opportunity_id=response.get('opportunity_id')
        )
        response = self.client.get(
            '/v2/quotes/compare?' + urlencode(data),
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_compare_quoutes_invalid_opportunity(self):
        data = dict(
            quotes='1,2',
            opportunity_id=1
        )
        response = self.client.get(
            '/v2/quotes/compare?' + urlencode(data),
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_compare_quotes_invalid_quotes(self):
        self.add_questions_answers()
        response = self.create_lead(self.user_id, self.header).json()
        data = dict(
            quotes='100,200',
            opportunity_id=response.get('opportunity_id')
        )
        response = self.client.get(
            '/v2/quotes/compare?' + urlencode(data),
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recommendation_quotes(self):
        self.add_questions_answers()
        response = self.create_lead(self.user_id, self.header).json()
        self.submit_answers(
            self.answers,
            opportunity_id=response.get('opportunity_id')
        ).json()
        data = dict(
            lead=response.get('lead_id'),
            opportunity_id=response.get('opportunity_id')
        )

        response = self.client.get(
            '/v2/quotes/recommendation?' + urlencode(data),
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.json()), 0)

    def test_reset_quotes(self):
        self.add_questions_answers()
        response = self.create_lead(self.user_id, self.header).json()
        self.submit_answers(
            self.answers,
            opportunity_id=response.get('opportunity_id')
        ).json()
        data = dict(
            lead=response.get('lead_id'),
            opportunity_id=response.get('opportunity_id'),
            suminsured=500000
        )

        response = self.client.get(
            '/v2/quotes/recommendation?' + urlencode(data),
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0].get('sum_insured'), 500000)

    def test_invalid_lead_recommended_quotes(self):
        data = dict(
            lead=1,
            opportunity_id=1
        )

        response = self.client.get(
            '/v2/quotes/recommendation?' + urlencode(data),
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_reset_quotes(self):
        self.add_questions_answers()
        response = self.create_lead(self.user_id, self.header).json()
        self.submit_answers(
            self.answers,
            opportunity_id=response.get('opportunity_id')
        ).json()
        data = dict(
            lead=response.get('lead_id'),
            opportunity_id=response.get('opportunity_id'),
            suminsured=50
        )

        response = self.client.get(
            '/v2/quotes/recommendation?' + urlencode(data),
            **self.header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])
