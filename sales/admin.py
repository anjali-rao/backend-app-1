# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin, messages
from django.utils.html import format_html

from sales.models import (
    Quote, Application, HealthInsurance, Member,
    Nominee
)

from payment.models import ApplicationRequestLog
from aggregator import PAYMENT_LINK_MAPPER

from utils import constants as Constants


class HealthInsuranceInline(admin.StackedInline):
    model = HealthInsurance


class MemberInlineAdmin(admin.TabularInline):
    model = Member
    can_delete = False
    max_num = 4


class NomineeInlineAdmin(admin.TabularInline):
    model = Nominee
    can_delete = False
    max_num = 2


class ApplicationRequestLogInline(admin.StackedInline):
    model = ApplicationRequestLog
    can_delete = False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'status', 'premium')
    raw_id_fields = ('lead', 'premium')
    list_filter = ('status',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'reference_no', 'application_type', 'status', 'terms_and_conditions',
        'aggregator_operation', 'payment_link', 'created')
    list_filter = ('application_type', 'terms_and_conditions', 'status')
    raw_id_fields = ('client', 'quote')
    search_fields = (
        'reference_no', 'quote__id', 'quote__lead__id', 'id',
        'client__phone_no', 'client__address__pincode__pincode',
        'client__address__pincode__city'
    )
    actions = ['send_to_Aggregator', 'generate_Aggregator_Payment_Link']
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
        inlines.append(
            ApplicationRequestLogInline(self.model, self.admin_site))
        return inlines

    def get_inline_class(self, keywords):
        return self._inlines_class_set.get(keywords)

    def send_to_Aggregator(self, request, queryset):
        for query in queryset:
            try:
                query.aggregator_operation()
                msz = Constants.SEND_TO_AGGREGATOR % (query.reference_no)
                message_class = messages.SUCCESS
            except Exception as e:
                msz = Constants.FAILED_TO_SEND_TO_AGGREGATOR % (
                    query.reference_no, str(e))
                message_class = messages.ERROR
            self.message_user(request, msz, message_class)

    def generate_Aggregator_Payment_Link(self, request, queryset):
        for query in queryset:
            try:
                query.application.insurer_operation()
                msz = Constants.PAYMENT_LINK_GENERATION % (
                    query.reference_no)
                message_class = messages.SUCCESS
            except Exception as e:
                msz = Constants.PAYMENT_LINK_GENERATION_FAILED % (
                    query.reference_no, str(e))
                message_class = messages.ERROR
            self.message_user(request, msz, message_class)

    def aggregator_operation(self, obj):
        filename = 'Yes' if hasattr(obj, 'application') else 'No'
        return format_html(
            '<img src="/static/admin/img/icon-{0}.svg" alt="True">', filename)

    def payment_link(self, obj):
        if hasattr(obj, 'application'):
            if obj.application.payment_ready:
                link = 'https://payment.goplannr.com/health/%s/%s' % (
                    PAYMENT_LINK_MAPPER.get(obj.application.company_name),
                    obj.application.id)
                return format_html('<a href="{0}">{0}</a>', link)
            return format_html(
                '<img src="/static/admin/img/icon-No.svg" alt="True">')
        return None


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
