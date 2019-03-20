# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import (
    Account, User, Campaign, UserDetails, Documents, Bank, BankAccount,
    BankBranch, Enterprise)


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
        'account', 'user_type', 'campaign', 'enterprise', 'is_active')
    list_filter = ('is_active', 'user_type')
    search_fields = (
        'account__phone_no', 'account__alternate_no', 'account__aadhar_no')
    raw_id_fields = ('account', 'enterprise', 'campaign')


@admin.register(UserDetails)
class UserDetailsAdmin(admin.ModelAdmin):
    list_display = ('user', 'agent_code', 'channel', 'status')
    list_filter = ('channel', 'status')
    search_fields = ('user__account__username', 'user__account__phone_no')
    raw_id_fields = ('user',)


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
