# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase


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
        response = requests.request("POST", url, data=payload, headers=headers)
        for row in response.json():
            self.assertNotEqual(row['response']['status_code'], '500')
