# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from sales.models import (
    Quote, Application
)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'status', 'premium')
    raw_id_fields = ('lead', 'premium')
    list_filter = ('status',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('reference_no', 'quote', 'status')
    search_fields = ('reference_no',)
    list_filter = ('status',)
