# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from crm.models import Lead, Contact, KYCDocument


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'amount', 'final_score')
    search_fields = ('user__account__phone_no', 'id', 'category__id')
    list_filter = ('category',)
    raw_id_fields = ('user', 'category', 'contact', 'customer_segment')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_no', 'email')
    search_fields = ('phone_no', 'user__account__phone_no')
    raw_id_fields = ('user', 'address',)


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ('contact', 'document_type', 'document_number')
    raw_id_fields = ('contact',)
    list_filter = ('document_type',)
    search_fields = ('docunent_number', 'contact__phone_no')
