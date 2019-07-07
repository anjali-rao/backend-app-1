# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from crm.models import Lead, Contact, Opportunity
from crm.opportunity.models import HealthInsurance
from content.models import Note
from utils.script import export_as_csv


class HealthInsuranceInline(admin.StackedInline):
    model = HealthInsurance

    can_delete = False

    def has_change_permission(self, request, obj=None):
        return False


class NotesInline(admin.TabularInline):
    model = Note
    can_delete = False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Opportunity)
class OpportunityInline(admin.ModelAdmin):
    list_display = ('lead', 'category')
    search_fields = (
        'lead__id', 'category__name', 'category__id',
        'lead__user__account__phone_no')
    raw_id_fields = ('lead', 'category')
    list_filter = ('category',)
    _inlines_class_set = dict(
        healthinsurance=HealthInsuranceInline
    )
    fk_fields = [
    'lead', 'lead__user',
    'lead__user__account', 'lead__user__enterprise',
    'lead__user__campaign', 'lead__contact',
    'lead__contact__address', 'lead__contact__address__pincode',
    'lead__contact__address__pincode__state', 'lead__category'
    ]
    actions = [export_as_csv]

    def get_inline_instances(self, request, obj=None):
        inlines = list()
        if obj is not None and hasattr(obj, obj.category_name):
            inline_class = self.get_inline_class(obj.category_name)
            inlines.append(inline_class(self.model, self.admin_site))
        return inlines

    def get_inline_class(self, keywords):
        return self._inlines_class_set.get(keywords)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('user', 'contact')
    search_fields = ('user__account__phone_no', 'id',)
    raw_id_fields = ('user', 'contact',)
    inlines = (NotesInline,)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'contact', 'phone_no', 'email', 'modified', 'created')
    search_fields = ('phone_no', 'user__account__phone_no', 'id', 'first_name')
    raw_id_fields = ('user', 'address',)

    def contact(self, obj):
        return obj.get_full_name()

# @admin.register(KYCDocument)
# class KYCDocumentAdmin(admin.ModelAdmin):
#     list_display = ('contact', 'document_type', 'document_number')
#     raw_id_fields = ('contact',)
#     list_filter = ('document_type',)
#     search_fields = ('docunent_number', 'contact__phone_no')
