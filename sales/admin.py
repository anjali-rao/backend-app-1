# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from sales.models import (
    Quote, Application, HealthInsurance, Member,
    Nominee
)


class HealthInsuranceInline(admin.StackedInline):
    model = HealthInsurance
    fk_name = "insurance"


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'status', 'premium')
    raw_id_fields = ('lead', 'premium')
    list_filter = ('status',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    model = Application

    def get_inline_instances(self, request, obj=None):
        if obj is not None:
            m_name = obj.insurance_object._meta.model_name
            if m_name == "healthinsurance":
                return [HealthInsuranceInline(self.model, self.admin_site), ]
        return []

# class ApplicationAdmin(admin.ModelAdmin):
#     list_display = ('reference_no', 'quote', 'status')
#     search_fields = ('reference_no',)
#     list_filter = ('status',)
# 
#     def get_inline_instances(self, request, obj=None):
#         '''
#         Returns our Thing Config inline
#         '''
#         if obj is not None:
#             m_name = obj.insurance_object._meta.model_name
#             if m_name == "healthinsurance":
#                 # return []
#                 return [HealthInsuranceInline(self.model, self.admin_site), ]
#         return []


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
