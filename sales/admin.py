# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin, messages
from django.utils.html import format_html

from sales.models import (
    Quote, Application, HealthInsurance, Member,
    Nominee, Policy, ProposerDocument)
from payment.models import ApplicationRequestLog
from utils import constants as Constants
from utils.script import export_as_csv


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
    list_display = ('opportunity', 'status', 'premium', 'ignore')
    search_fields = (
        'opportunity__lead__user__account__phone_no', 'premium_id',
        'opportunity__lead__contact__phone_no')
    raw_id_fields = ('opportunity', )
    list_filter = ('status', 'ignore')
    readonly_fields = ('premium_id', 'content_type', 'ignore')
    can_delete = False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'reference_no', 'application_type', 'variant_name', 'status', 'stage',
        'terms_and_conditions', 'aggregator_operation', 'payment_link',
        'payment_captured', 'created')
    list_filter = ('application_type', 'terms_and_conditions', 'status')
    raw_id_fields = ('proposer', 'quote')
    search_fields = (
        'reference_no', 'quote__id', 'quote__opportunity__lead__id', 'id',
        'proposer__phone_no', 'proposer__address__pincode__pincode',
        'proposer__first_name', 'proposer__last_name', 'proposer__middle_name'
        'proposer__phone_no', 'proposer__address__pincode__city',
        'quote__opportunity__lead__user__account__phone_no',
        'quote__opportunity__lead__user__account__first_name',
        'quote__opportunity__lead__user__account__middle_name',
        'quote__opportunity__lead__user__account__last_name',
    )
    fk_fields = [
        'proposer', 'quote',
        'proposer__user', 'proposer__user',
        'proposer__user__account', 'proposer__user__enterprise',
        'proposer__user__campaign', 'proposer__address',
        'proposer__address__pincode',
        'proposer__address__pincode__state',
        'quote__opportunity', 'quote__opportunity__lead',
        'quote__opportunity__lead__user',
        'quote__opportunity__lead__user__account',
        'quote__opportunity__lead__user__enterprise',
        'quote__opportunity__lead__user__campaign',
        'quote__opportunity__lead__contact',
        'quote__opportunity__lead__contact__address',
        'quote__opportunity__lead__contact__address__pincode',
        'quote__opportunity__lead__contact__address__pincode__state',
        'quote__opportunity__lead__category'
    ]
    actions = ['send_to_Aggregator', 'generate_Aggregator_Payment_Link',
    export_as_csv]
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

    def variant_name(self, obj):
        return obj.quote.premium.product_variant.__str__()

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
        filename = 'yes' if hasattr(obj, 'application') else 'no'
        return format_html(
            '<img src="/static/admin/img/icon-{0}.svg" alt="True">', filename)

    def payment_link(self, obj):
        if hasattr(obj, 'application'):
            if obj.application.payment_ready:
                return format_html(
                    '<a href="{0}" target="__newtab">{1}</a>',
                    obj.application.get_payment_link(), 'Open Link')
            return format_html(
                '<img src="/static/admin/img/icon-no.svg" alt="True">')
        return None

    def payment_captured(self, obj):
        if hasattr(obj, 'application'):
            if obj.application.payment_captured:
                return format_html(
                    '<a href="{0}">{0}</a>',
                    obj.application.payment_captured)
            return format_html(
                '<img src="/static/admin/img/icon-no.svg" alt="True">')
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


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('application', 'policy_number', 'policy_file', 'created')
    search_fields = (
        'application__quote__lead__user_phone_no',
        'application__proposer_phone_no', 'application__proposer_email')
    list_filter = ('application__quote__opportunity__category',)
    raw_id_fields = ('application',)


@admin.register(ProposerDocument)
class ProposerDocumentAdmin(admin.ModelAdmin):
    list_display = ('contact', 'document_type', 'file')
    search_fields = ('contact__phone_no',)
    raw_id_fields = ('contact',)
    list_filter = ('document_type',)
