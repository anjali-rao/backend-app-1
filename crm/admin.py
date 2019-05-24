# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from crm.models import Lead, Contact, KYCDocument
from crm.leads.models import HealthInsurance


class HealthInsuranceInline(admin.StackedInline):
    model = HealthInsurance

    can_delete = False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'pincode')
    search_fields = ('user__account__phone_no', 'id', 'category__id')
    list_filter = ('category',)
    raw_id_fields = ('user', 'category', 'contact',)
    _inlines_class_set = dict(
        healthinsurance=HealthInsuranceInline
    )

    def get_inline_instances(self, request, obj=None):
        inlines = list()
        if obj is not None and hasattr(obj, obj.category_name):
            inline_class = self.get_inline_class(obj.category_name)
            inlines.append(inline_class(self.model, self.admin_site))
        return inlines

    def get_inline_class(self, keywords):
        return self._inlines_class_set.get(keywords)


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
