# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import Account, User


@admin.register(User)
class GoPlannerUserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email',
    )
    search_fields = ('username', 'email', 'account__phone_no')
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


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('phone_no', 'pan_no', 'gender')
    list_filter = ('gender', 'pincode')
    search_fields = ('phone_no', 'alternate_no', 'aadhar_no')
