# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from product.models import (
    Company, Category, CompanyDetails, CompanyCategory, ProductVariant,
    CustomerSegment, FeatureMaster, Feature, SumInsuredMaster,
    DeductibleMaster, Premium
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'website')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(CompanyDetails)
class CompanyDetailsAdmin(admin.ModelAdmin):
    list_display = ('company', 'formation_year')
    raw_id_fields = ('company', )


@admin.register(CompanyCategory)
class ComapanyCategoryAdmin(admin.ModelAdmin):
    list_display = ('category', 'company', 'claim_settlement')
    raw_id_fields = ('category', 'company')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('company_category', 'name', 'parent')
    raw_id_fields = ('company_category', 'parent')


@admin.register(CustomerSegment)
class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(FeatureMaster)
class FeatureMasterAdmin(admin.ModelAdmin):
    list_display = ('category', 'name', 'description')
    search_fields = ('category__id',)
    raw_id_fields = ('category',)


@admin.register(Feature)
class Feature(admin.ModelAdmin):
    list_display = ('feature_master', 'product_variant')
    search_fields = ('feature_master__name',)
    raw_id_fields = ('feature_master', 'product_variant')


@admin.register(SumInsuredMaster)
class SumInsuredMasterAdmin(admin.ModelAdmin):
    list_display = ('number', 'text')


@admin.register(DeductibleMaster)
class DeductibleMasterAdmin(admin.ModelAdmin):
    list_display = ('number', 'text')


@admin.register(Premium)
class PremiumAdmin(admin.ModelAdmin):
    list_display = ('product_variant', 'sum_insured', 'min_age', 'max_age')
    search_fields = ('product_variant__id',)
    raw_id_fields = ('product_variant', 'sum_insured', 'deductible')
