# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from sales.models import (
    Quote, QuoteFeature, Client, KYCDocuments, Application
)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'status', 'premium')
    raw_id_fields = ('lead', 'premium')


@admin.register(QuoteFeature)
class QuoteFeatureAdmin(admin.ModelAdmin):
    list_display = ('quote', 'feature', 'score')
    raw_id_fields = ('quote', 'feature')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'contact_no')
    search_fields = ('contact_no', 'document_number')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('reference_no', 'quote', 'status')
    search_fields = ('reference_no',)
    list_filter = ('status',)


@admin.register(KYCDocuments)
class KYCDocumentsAdmin(admin.ModelAdmin):
    list_display = ('client',)
    raw_id_fields = ('client',)
    list_filter = ('doc_type',)
