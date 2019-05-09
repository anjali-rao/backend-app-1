# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from content.models import (
    Faq, HelpFile, ContactUs, NetworkHospital, NewsletterSubscriber,
    PromoBook)


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
    list_display = ('full_name', 'phone_no', 'email', 'created')
    search_fields = ('phone_no', 'email', 'full_name')


@admin.register(NetworkHospital)
class NetworkHospitalAdmin(admin.ModelAdmin):
    list_display = ('name','contact_number')
    search_fields = ('name',)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'unsubscribe')
    search_fields = ('email',)
    list_filter = ('unsubscribe',)


@admin.register(PromoBook)
class PromoBookAdmin(admin.ModelAdmin):
    list_display = ('phone_no',)
    search_fields = ('phone_no',)
