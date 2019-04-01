# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from content.models import (
    Faq, HelpFile, ContactUs, NetworkHospital)


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer')
    search_fields = ('question', 'id')


@admin.register(HelpFile)
class HelpFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type')
    search_fields = ('category',)
    list_filter = ('file_type',)


@admin.register(ContactUs)
class ContactUs(admin.ModelAdmin):
    list_display = ('title', 'value_type')
    search_fields = ('title',)
    list_filter = ('value_type',)


@admin.register(NetworkHospital)
class NetworkHospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'contact_number')
    search_fields = ('name', 'city')
