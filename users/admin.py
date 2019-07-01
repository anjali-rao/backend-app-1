# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from extended_filters.filters import DateRangeFilter

from users.models import (
    Account, User, Campaign, AccountDetail, KYCDocument, BankAccount,
    Enterprise, State, Pincode, Address, IPAddress, Referral, PromoCode)


@admin.register(Account)
class GoPlannerAccountAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'phone_no', 'pan_no', 'gender'
    )
    search_fields = ('username', 'email', 'phone_no')
    fieldsets = (
        (None, {'fields': ('username', 'password', 'phone_no')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Permissions', {
            'classes': ('collapse',),
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'groups',
                'user_permissions',
            )
        })
    )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'account', 'user_type', 'campaign', 'is_active', 'created')
    list_filter = (
        'is_active', 'user_type', ('created', DateRangeFilter),
        ('modified', DateRangeFilter))
    search_fields = (
        'account__phone_no', 'account__alternate_no', 'account__aadhar_no')
    raw_id_fields = ('account', 'campaign', 'enterprise')


@admin.register(AccountDetail)
class AccountDetailsAdmin(admin.ModelAdmin):
    list_display = ('account', 'agent_code', 'channel', 'status')
    list_filter = ('channel', 'status')
    search_fields = ('account__username', 'user__account__phone_no')
    raw_id_fields = ('account',)


@admin.register(KYCDocument)
class KYCDocumentsAdmin(admin.ModelAdmin):
    list_display = ('account', 'document_type', 'file')
    search_fields = ('account__username', 'account__phone_no')
    raw_id_fields = ('account',)
    list_filter = ('document_type',)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch', 'default')
    search_fields = ('user__username', 'user__account__phone_no')
    raw_id_fields = ('user', 'branch')
    list_filter = ('default',)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('description',)


@admin.register(Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ('name', 'promocode', 'enterprise_type', 'hexa_code')
    search_fields = ('name', 'promocode__code',)
    list_filter = ('enterprise_type',)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)
    readonly_fields = ('name',)


@admin.register(Pincode)
class PincodeAdmin(admin.ModelAdmin):
    list_display = ('pincode', 'city', 'state',)
    search_fields = ('pincode', 'state__name', 'city')
    list_filter = ('state__name',)
    raw_id_fields = ('state',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('flat_no', 'street', 'landmark')
    search_fields = ('pincode__pincode', 'pincode__state', 'pincode__city')
    raw_id_fields = ('pincode',)
    list_filter = ('pincode__state',)


@admin.register(IPAddress)
class IPAddressAdmin(admin.ModelAdmin):
    list_display = (
        'ip_address', 'company_name', 'authentication_required',
        'blocked')
    raw_id_fields = ('account',)
    search_fields = ('ip_address',)
    list_filter = ('authentication_required', 'blocked')


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('code', 'reference_code',)
    raw_id_fields = ('user',)
    search_fields = ('code', 'reference_code')


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code',)
    search_fields = ('code',)
