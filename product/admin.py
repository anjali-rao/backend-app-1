# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from product.models import Company, Category


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'website')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)