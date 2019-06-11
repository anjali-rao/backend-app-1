# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from payment.models import ApplicationPayment, ApplicationRequestLog


@admin.register(ApplicationPayment)
class ApplicationPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'application', 'transaction_reference_no', 'merchant_txn_id',
        'payment_mode')
    list_filter = ('application__application_type',)


@admin.register(ApplicationRequestLog)
class ApplicationRequestLogAdmin(admin.ModelAdmin):
    list_display = ('application', 'request_type', 'url')
    search_fields = ('application__reference_no', 'application__id',)
    list_filter = ('application__application_type',)
