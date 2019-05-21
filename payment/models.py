# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from utils.models import BaseModel, models
from utils import constants as Constants, get_choices

from django.contrib.postgres.fields import JSONField


class ApplicationRequestLog(BaseModel):
    application = models.ForeignKey(
        'sales.application', on_delete=models.PROTECT)
    request_type = models.CharField(
        max_length=32, choices=get_choices(Constants.REQUEST_CHOICES))
    url = models.URLField(null=True, blank=True)
    payload = JSONField(default=dict)
    response = JSONField(default=dict)

    class Meta:
        ordering = ('-modified',)


class Payment(BaseModel):
    application = models.ForeignKey(
        'sales.application', on_delete=models.PROTECT)
    merchant_txn_id = models.CharField(max_length=126)
    transaction_reference_no = models.CharField(max_length=64)
    transaction_id = models.CharField(max_length=64)
    payment_mode = models.CharField(max_length=64)
    amount = models.CharField(max_length=63)
    status = models.CharField(max_length=32)
    response = JSONField(default=dict)

    class Meta:
        ordering = ('-modified',)
