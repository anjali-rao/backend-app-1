# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from utils.models import BaseModel, models

from django.contrib.postgres.fields import JSONField


class RequestLog(BaseModel):
    url = models.URLField()
    amount = models.CharField(max_length=32)
    payload = JSONField(default=dict)
    response = JSONField(default=dict)


class Payment(BaseModel):
    merchant_txn_id = models.CharField(max_length=126)
    transaction_reference_no = models.CharField(max_length=64)
    transaction_id = models.CharField(max_length=64)
    payment_mode = models.CharField(max_length=64)
    amount = models.CharField(max_length=63)
    status = models.CharField(max_length=32)
    response = JSONField(default=dict)
