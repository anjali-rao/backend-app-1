# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from sales.models import (
    Quote, Application, HealthInsurance, Member,
    Nominee
)


class HealthInsuranceInline(admin.StackedInline):
    model = HealthInsurance


class MemberInlineAdmin(admin.TabularInline):
    model = Member
    max_num = 4


class NomineeInlineAdmin(admin.TabularInline):
    model = Nominee
    max_num = 2


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'status', 'premium')
    raw_id_fields = ('lead', 'premium')
    list_filter = ('status',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'reference_no', 'application_type', 'status', 'terms_and_conditions',
        'created')
    list_filter = ('application_type', 'terms_and_conditions', 'status')
    raw_id_fields = ('client', 'quote')
    search_fields = (
        'reference_no', 'quote__id', 'quote__lead__id', 'id',
        'client__phone_no',
        'client__address__pincode__pincode',
        'client__address__pincode__city'
    )
    _inlines_class_set = dict(
        healthinsurance=HealthInsuranceInline
    )

    def get_inline_instances(self, request, obj=None):
        inlines = [
            NomineeInlineAdmin(self.model, self.admin_site),
            MemberInlineAdmin(self.model, self.admin_site)]
        if obj is not None and hasattr(obj, obj.application_type):
            inline_class = self.get_inline_class(obj.application_type)
            inlines.append(inline_class(
                self.model, self.admin_site))
        return inlines

    def get_inline_class(self, keywords):
        return self._inlines_class_set.get(keywords)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('application', 'first_name', 'age', 'occupation',)
    search_fields = ('application__quote__id', 'first_name', 'middle_name')
    list_filter = ('ignore',)


@admin.register(Nominee)
class NomineeAdmin(admin.ModelAdmin):
    list_display = ('application', 'first_name')
    search_fields = ('application__quote__id', 'application__reference_no')
    list_filter = ('ignore',)
