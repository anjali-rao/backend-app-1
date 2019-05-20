# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from payment.models import Payment


@admin.register(Payment)
class Payment(admin.ModelAdmin):
    list_display = (
        'transaction_reference_no', 'merchant_txn_id', 'payment_mode')
