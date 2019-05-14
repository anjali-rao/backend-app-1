# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from content.models import (
    Faq, HelpFile, ContactUs, NetworkHospital, NewsletterSubscriber,
    PromoBook, HelpLine, Playlist, EnterprisePlaylist, Article,
    Coverages)


@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer')
    search_fields = ('question', 'id')


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


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'unsubscribe')
    search_fields = ('email',)
    list_filter = ('unsubscribe',)


@admin.register(PromoBook)
class PromoBookAdmin(admin.ModelAdmin):
    list_display = ('phone_no',)
    search_fields = ('phone_no',)


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
    raw_id_fields = ('playlist',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('heading', 'tags', 'url')
    search_fields = ('tags', 'heading')
    list_filter = ('tags',)


@admin.register(Coverages)
class CoveragesAdmin(admin.ModelAdmin):
    list_display = ('company_category', 'name',)
