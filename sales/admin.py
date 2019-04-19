# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from sales.models import (
    Quote, Application, HealthInsurance, TravelInsurance, Member
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


@admin.register(HealthInsurance)
class HealthInsuranceAdmin(admin.ModelAdmin):
    list_display = ('application',)
    search_fields = ('application__quote__id',)


@admin.register(TravelInsurance)
class TravelInsuranceAdmin(admin.ModelAdmin):
    list_display = ('application',)
    search_fields = ('application__quote__id',)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('application', 'first_name', 'age', 'occupation',)
    search_fields = ('application__quote__id', 'first_name', 'middle_name')
    list_filter = ('ignore',)
