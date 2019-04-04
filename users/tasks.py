import json
import urllib
import requests

from goplannr.settings import SMS_API_KEY, SMS_API


def send_sms(phone_no, message):
    json_data = {
        "sms": [{
            "to": phone_no,
            "message": message,
            'sender': 'GOPLNR'
        }]
    }
    url = '%s%s' % (SMS_API, SMS_API_KEY)
    url += "&method=sms.json&json=" + urllib.parse.quote(json.dumps(json_data))
    response = requests.post(url)
    return response.json()
