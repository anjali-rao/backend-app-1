# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import (
    Account, User, Campaign, AccountDetails, Documents, Bank, BankAccount,
    BankBranch, Enterprise, SubcriberEnterprise, State, Pincode, ContactUs)


@admin.register(Account)
class GoPlannerAccountAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'phone_no', 'pan_no', 'gender'
    )
    search_fields = ('username', 'email', 'phone_no')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email',)}),
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
        'account', 'user_type', 'campaign', 'is_active')
    list_filter = ('is_active', 'user_type')
    search_fields = (
        'account__phone_no', 'account__alternate_no', 'account__aadhar_no')
    raw_id_fields = ('account', 'campaign')


@admin.register(AccountDetails)
class AccountDetailsAdmin(admin.ModelAdmin):
    list_display = ('account', 'agent_code', 'channel', 'status')
    list_filter = ('channel', 'status')
    search_fields = ('account__username', 'user__account__phone_no')
    raw_id_fields = ('account',)


@admin.register(Documents)
class DocumentsAdmin(admin.ModelAdmin):
    list_display = ('user', 'doc_type', 'file')
    search_fields = ('user__username', 'user__account__phone_no')
    raw_id_fields = ('user',)
    list_filter = ('doc_type',)


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('name', 'is_active')


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch', 'default')
    search_fields = ('user__username', 'user__account__phone_no')
    raw_id_fields = ('user', 'branch')
    list_filter = ('default',)


@admin.register(BankBranch)
class BankBranchAdmin(admin.ModelAdmin):
    list_display = ('bank', 'branch_name', 'ifsc', 'city', 'micr')
    search_fields = (
        'branch_name__user__username', 'branch_name__user__account__phone_no')
    raw_id_fields = ('bank',)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('description',)


@admin.register(Enterprise)
class EnterpriseAdmin(admin.ModelAdmin):
    list_display = ('name', 'hexa_code')


@admin.register(SubcriberEnterprise)
class SubcriberEnterpriseAdmin(admin.ModelAdmin):
    list_display = ('name', 'hexa_code')


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)
    readonly_fields = ('name',)


@admin.register(Pincode)
class PincodeAdmin(admin.ModelAdmin):
    list_display = ('pincode', 'city', 'state', 'city_type')
    search_fields = ('pincode', 'state__name', 'city')
    list_filter = ('state__name', 'city_type')
    raw_id_fields = ('state',)


@admin.register(ContactUs)
class ContactUs(admin.ModelAdmin):
    list_display = ('phone_no', 'email')
