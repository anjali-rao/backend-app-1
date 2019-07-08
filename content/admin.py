# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.html import format_html

from content.models import (
    Faq, HelpFile, ContactUs, NetworkHospital, NewsletterSubscriber,
    PromoBook, HelpLine, Playlist, EnterprisePlaylist, Article,
    Coverages, Note, Appointment, Bank, BankBranch, Collateral)
from utils.script import export_as_csv


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ('category', 'question', 'answer')
    search_fields = ('question', 'id')
    list_filter = ('category',)


@admin.register(HelpFile)
class HelpFileAdmin(admin.ModelAdmin):
    list_display = ('product_variant', 'file_type')
    search_fields = (
        'product_variant__company_category__category__name',
        'product_variant__company_category__company__name')
    list_filter = (
        'file_type', 'product_variant__company_category__category__name',
        'product_variant__company_category__company__name')
    raw_id_fields = ('product_variant',)


@admin.register(ContactUs)
class ContactUs(admin.ModelAdmin):
    list_display = ('full_name', 'phone_no', 'email', 'created')
    search_fields = ('phone_no', 'email', 'full_name')


@admin.register(NetworkHospital)
class NetworkHospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_number', 'company', 'pincode')
    search_fields = (
        'name', 'contact_number', 'company__name', 'pincode__pincode',
        'pincode__city', 'pincode__state__name')
    list_filter = ('pincode__state__name', )
    raw_id_fields = ('pincode', 'company')
    fk_fields = ['company', 'pincode', 'pincode__state']
    actions = [export_as_csv]


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'unsubscribe')
    search_fields = ('email',)
    list_filter = ('unsubscribe',)


@admin.register(PromoBook)
class PromoBookAdmin(admin.ModelAdmin):
    list_display = ('phone_no',)
    search_fields = ('phone_no',)
    actions = [export_as_csv]


@admin.register(HelpLine)
class HelpLineAdmin(admin.ModelAdmin):
    list_display = ('company', 'number')
    search_fields = ('number', 'company__name')
    list_filter = ('company__name',)
    raw_id_fields = ('company',)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'playlist_type', 'url')
    search_fields = ('name', 'url')
    list_filter = ('playlist_type',)


@admin.register(EnterprisePlaylist)
class EnterprisePlaylist(admin.ModelAdmin):
    list_display = ('enterprise', 'playlist')
    search_fields = ('enterprise_id',)
    raw_id_fields = ('playlist', 'enterprise')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('heading', 'tags', 'url')
    search_fields = ('tags', 'heading')
    list_filter = ('tags',)


@admin.register(Coverages)
class CoveragesAdmin(admin.ModelAdmin):
    list_display = ('company_category', 'name',)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'title',)
    search_fields = (
        'title', 'lead__id', 'lead__user__phone_no', 'lead__contact__phone_no',
        'lead__contact__email'
    )
    raw_id_fields = ('lead',)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_no', 'date', 'category')
    raw_id_fields = ('lead', 'user')
    search_fields = ('phone_no', 'name', 'user__phone_no')


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('name', 'is_active')
    search_fields = ('name',)

    class Meta:
        ordering = ('name',)


@admin.register(BankBranch)
class BankBranchAdmin(admin.ModelAdmin):
    list_display = ('bank', 'branch_name', 'ifsc', 'city')
    search_fields = ('branch_name', 'bank__name', 'ifsc', 'city')
    raw_id_fields = ('bank',)
    list_filter = ('bank__name',)


@admin.register(Collateral)
class CollateralAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'collateral_type', 'collateral_file_type', 'url', 'promocode')
    search_fields = (
        'name', 'url', 'collateral_type', 'collateral_file_type', 'promocode')
    list_filter = ('collateral_type', 'collateral_file_type', 'promocode')
