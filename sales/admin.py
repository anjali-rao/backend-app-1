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
    model = Application

    def get_inline_instances(self, request, obj=None):
        inlines = [NomineeInlineAdmin, MemberInlineAdmin]
        if obj is not None:
            m_name = obj.insurance_object._meta.model_name
            if m_name == "healthinsurance":
                inlines.append(HealthInsuranceInline(
                    self.model, self.admin_site))
        return inlines


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
