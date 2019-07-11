# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from payment.models import ApplicationPayment, ApplicationRequestLog
from utils.script import export_as_csv


@admin.register(ApplicationPayment)
class ApplicationPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'application', 'transaction_reference_no', 'merchant_txn_id',
        'payment_mode')
    list_filter = ('application__application_type',)
    fk_fields = [
    'application', 'application__proposer', 'application__quote',
    'application__proposer__user', 'application__proposer__user',
    'application__proposer__user__account', 'application__proposer__user__enterprise',
    'application__proposer__user__campaign', 'application__proposer__address',
    'application__proposer__address__pincode',
    'application__proposer__address__pincode__state',
    'application__quote__opportunity', 'application__quote__opportunity__lead',
    'application__quote__opportunity__lead__user',
    'application__quote__opportunity__lead__user__account',
    'application__quote__opportunity__lead__user__enterprise',
    'application__quote__opportunity__lead__user__campaign',
    'application__quote__opportunity__lead__contact',
    'application__quote__opportunity__lead__contact__address',
    'application__quote__opportunity__lead__contact__address__pincode',
    'application__quote__opportunity__lead__contact__address__pincode__state',
    'application__quote__opportunity__lead__category'
    ]
    actions = [export_as_csv]


@admin.register(ApplicationRequestLog)
class ApplicationRequestLogAdmin(admin.ModelAdmin):
    list_display = ('application', 'request_type', 'url')
    search_fields = ('application__reference_no', 'application__id',)
    list_filter = ('application__application_type',)
