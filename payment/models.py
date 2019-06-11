# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from utils.models import BaseModel, models
from utils import constants as Constants, get_choices

from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now


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


class ApplicationPayment(BaseModel):
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


class Transaction(BaseModel):
    payment_id = models.CharField(max_length=128)
    amount = models.FloatField(default=0.0)
    transaction_id = models.CharField(max_length=128, blank=True)
    model_name = models.CharField(max_length=64)
    app_name = models.CharField(max_length=64)


@receiver(post_save, sender=ApplicationPayment, dispatch_uid="action%s" % str(
    now()))
def application_payment_post_save(sender, instance, created, **kwargs):
    if created:
        data = dict(
            payment_id=instance.id, amount=instance.amount,
            transaction_id=instance.transaction_id,
            model_name=instance.__class__.__name__, app_name='payment')
        Transaction.objects.create(**data)
