# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from utils.model import BaseModel, models
from utils.constants import COMPANY_UPLOAD_PATH


class Category(BaseModel):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class Company(BaseModel):
    name = models.CharField(max_length=256)
    logo = models.ImageField(upload_to=COMPANY_UPLOAD_PATH)
    hexa_code = models.CharField(max_length=8)
    short_name = models.CharField(max_length=128)
    website = models.URLField(null=True, blank=True)
    spoc = models.TextField(null=True, blank=True)
    toll_free_number = models.CharField(max_length=50, null=True, blank=True)
    long_description = models.TextField(null=True, blank=True)
    small_description = models.TextField(null=True, blank=True)
    categories = models.ManyToManyField(Category)

    def __unicode__(self):
        return self.name


class CompanyDetails(BaseModel):
    company = models.OneToOneField(Company)
    fact_file = models.TextField(null=True, blank=True)
    joint_venture = models.TextField(null=True, blank=True)
    formation_year = models.CharField(max_length=4, null=True, blank=True)
    market_share = models.TextField(null=True, blank=True)
    claim_settlement = models.TextField(null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)
    is_offer = models.BooleanField(default=False)


