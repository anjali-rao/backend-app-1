# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from extended_filters.filters import CheckBoxListFilter

from product.models import (
    Company, Category, CompanyDetails, CompanyCategory, ProductVariant,
    CustomerSegment, FeatureMaster, Feature, SumInsuredMaster,
    DeductibleMaster, HealthPremium, FeatureCustomerSegmentScore
)
from utils.script import export_as_csv


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'website', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    actions = ['mark_as_active', 'mark_as_inactive']

    def mark_as_active(self, request, queryset):
        queryset.update(is_active=True)

    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    actions = ['mark_as_active', 'mark_as_inactive']

    def mark_as_active(self, request, queryset):
        queryset.update(is_active=True)

    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(CompanyDetails)
class CompanyDetailsAdmin(admin.ModelAdmin):
    list_display = ('company', 'formation_year')
    raw_id_fields = ('company', )


@admin.register(CompanyCategory)
class ComapanyCategoryAdmin(admin.ModelAdmin):
    list_display = ('category', 'company', 'claim_settlement')
    raw_id_fields = ('category', 'company')
    search_fields = ('category__name', 'company__name')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'company_category')
    raw_id_fields = ('company_category',)
    list_filter = ('name', 'is_active', 'online_process')


@admin.register(CustomerSegment)
class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(FeatureMaster)
class FeatureMasterAdmin(admin.ModelAdmin):
    list_display = ('category', 'name', 'short_description', 'order')
    search_fields = ('category__id',)
    raw_id_fields = ('category',)
    fk_fields = ['category']
    actions = [export_as_csv]


@admin.register(Feature)
class Feature(admin.ModelAdmin):
    list_display = ('feature_master', 'product_variant',)
    search_fields = ('feature_master__name', 'product_variant__name')
    raw_id_fields = ('feature_master', 'product_variant')
    list_filter = ('product_variant__name', 'feature_master__name',)
    fk_fields = [
        'feature_master', 'feature_master__category',
        'product_variant', 'product_variant__company_category',
        'product_variant__company_category__company',
        'product_variant__company_category__category',
    ]
    actions = [export_as_csv]


@admin.register(SumInsuredMaster)
class SumInsuredMasterAdmin(admin.ModelAdmin):
    list_display = ('number', 'text')


@admin.register(DeductibleMaster)
class DeductibleMasterAdmin(admin.ModelAdmin):
    list_display = ('number', 'text')


@admin.register(HealthPremium)
class HealthPremiumAdmin(admin.ModelAdmin):
    list_display = (
        'product_variant', 'sum_insured', 'age_range', 'citytier',
        'base_premium')
    search_fields = (
        'product_variant__id', 'product_variant__name',
        'base_premium')
    raw_id_fields = ('product_variant', 'deductible')
    ordering = ('sum_insured',)
    list_filter = [
        ('product_variant', CheckBoxListFilter),
        'online_process', 'is_active',
        ('product_variant__company_category__company',
        CheckBoxListFilter), ('sum_insured', CheckBoxListFilter),
        'adults', 'childrens', 'citytier', 'ignore']
    fk_fields = ['product_variant', 'product_variant__company_category',
        'product_variant__company_category__category',
        'product_variant__company_category__company']
    actions = [export_as_csv]


@admin.register(FeatureCustomerSegmentScore)
class FeatureCustomerSegmentScoreAdmin(admin.ModelAdmin):
    list_display = ('feature_master', 'customer_segment', 'score')
    raw_id_fields = ('feature_master',)
    fk_fields = [
        'feature_master', 'feature_master__category',
        'product_variant', 'product_variant__company_category',
        'product_variant__company_category__company',
        'product_variant__company_category__category',
        'customer_segment'
    ]
    actions = [export_as_csv]
