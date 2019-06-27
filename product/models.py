# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import constants as Constants, get_choices

from django.utils.functional import cached_property
from django.contrib.postgres.fields import IntegerRangeField
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.fields import GenericRelation


class Category(BaseModel):
    name = models.CharField(max_length=128, db_index=True)
    description = models.TextField(null=True, blank=True)
    logo = models.ImageField(
        upload_to=Constants.CATEGORY_UPLOAD_PATH,
        default=Constants.DEFAULT_LOGO)
    hexa_code = models.CharField(
        max_length=8, default=Constants.DEFAULT_HEXA_CODE)
    is_active = models.BooleanField(default=False)
    commission = models.FloatField(default=Constants.DEFAULT_COMMISSION)

    def __str__(self):
        return self.name


class Company(BaseModel):
    name = models.CharField(max_length=128, db_index=True)
    short_name = models.CharField(max_length=128)
    categories = models.ManyToManyField('product.Category')
    logo = models.ImageField(
        upload_to=Constants.COMPANY_UPLOAD_PATH,
        default=Constants.DEFAULT_LOGO)
    hexa_code = models.CharField(
        max_length=8, default=Constants.DEFAULT_HEXA_CODE)
    website = models.URLField(null=True, blank=True)
    spoc = models.TextField(null=True, blank=True)
    toll_free_number = ArrayField(
        models.CharField(max_length=32), default=list, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    long_description = models.TextField(null=True, blank=True)
    small_description = models.TextField(null=True, blank=True)
    commission = models.FloatField(default=0.0)

    def __str__(self):
        return self.name


class CompanyDetails(BaseModel):
    company = models.OneToOneField('product.Company', on_delete=models.CASCADE)
    fact_file = models.TextField(null=True, blank=True)
    joint_venture = models.TextField(null=True, blank=True)
    formation_year = models.CharField(max_length=4, null=True, blank=True)
    market_share = models.TextField(null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)


class CompanyCategory(BaseModel):
    category = models.ForeignKey('product.Category', on_delete=models.CASCADE)
    company = models.ForeignKey('product.Company', on_delete=models.CASCADE)
    claim_settlement = models.CharField(max_length=128, null=True, blank=True)
    offer_flag = models.BooleanField(default=False)

    class Meta:
        unique_together = ('category', 'company')

    def __str__(self):
        return '%s - %s' % (self.company.short_name, self.category.name)


class ProductVariant(BaseModel):
    company_category = models.ForeignKey(
        'product.CompanyCategory', null=True, blank=True,
        on_delete=models.CASCADE)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=256, default="")
    parent_product = models.CharField(
        max_length=128, null=True, blank=True, default='GoPlannr')
    feature_variant = models.CharField(max_length=256, default='base')
    short_description = models.CharField(max_length=128, null=True, blank=True)
    long_description = models.TextField(null=True, blank=True)
    aggregator_available = models.BooleanField(default=False)
    chronic = models.BooleanField(default=True)

    def get_product_details(self):
        return {
            'name': self.product_short_name,
            'company': self.company_category.company.name,
            'logo': self.logo, 'variant_name': self.product_short_name
        }

    @cached_property
    def logo(self):
        from goplannr.settings import DEBUG
        return (
            Constants.DEBUG_HOST if DEBUG else ''
        ) + self.company_category.company.logo.url

    @cached_property
    def product_short_name(self):
        return self.name

    def get_basic_details(self):
        return dict(
            toll_free_number=', '.join(
                self.company_category.company.toll_free_number),
            brochure=self.get_help_file('sales_brochure'),
            claim_form=self.get_help_file('claim_form'))

    def get_help_file(self, file_type):
        from content.models import HelpFile
        helpfile = HelpFile.objects.filter(
            product_variant_id=self.id, file_type=file_type).first()
        return helpfile.file.url if helpfile else '-'

    def __str__(self):
        return self.product_short_name


class CustomerSegment(BaseModel):
    name = models.CharField(max_length=128, db_index=True)

    def __str__(self):
        return self.name


class FeatureMaster(BaseModel):
    category = models.ForeignKey(
        'product.Category', null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=127, default="")
    order = models.IntegerField(default=1)
    feature_type = models.CharField(
        max_length=32, default='Others',
        choices=get_choices(Constants.FEATURE_TYPES))
    short_description = models.CharField(max_length=128, null=True, blank=True)
    long_description = models.TextField(null=True, blank=True)

    def __str__(self):
        return "%s - %s" % (
            self.name, self.category.name)

    class Meta:
        ordering = ('order',)


class Feature(BaseModel):
    feature_master = models.ForeignKey(
        'product.FeatureMaster', null=True, blank=True,
        on_delete=models.CASCADE)
    product_variant = models.ForeignKey(
        'product.ProductVariant', null=True, blank=True,
        on_delete=models.CASCADE)
    rating = models.FloatField(default=0.0)
    short_description = models.CharField(max_length=156, null=True, blank=True)
    long_description = models.CharField(max_length=512, null=True, blank=True)

    class Meta:
        ordering = ('feature_master__order',)

    def __str__(self):
        return "%s - %s" % (
            self.product_variant.name, self.feature_master.name)


class FeatureCustomerSegmentScore(BaseModel):
    feature_master = models.ForeignKey(
        'product.FeatureMaster', on_delete=models.CASCADE)
    customer_segment = models.ForeignKey(
        'product.CustomerSegment', on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)

    def __str__(self):
        return '%s - %s' % (
            self.feature_master.name, self.customer_segment.name)


class SumInsuredMaster(models.Model):
    text = models.CharField(max_length=64)
    number = models.IntegerField()

    def __str__(self):
        return self.text


class DeductibleMaster(BaseModel):
    text = models.CharField(max_length=100)
    number = models.IntegerField()

    def __str__(self):
        return self.text


class HealthPremium(BaseModel):
    product_variant = models.ForeignKey(
        'product.ProductVariant', null=True, blank=True,
        on_delete=models.CASCADE)
    deductible = models.ForeignKey(
        'product.DeductibleMaster', null=True, blank=True,
        on_delete=models.CASCADE)
    sum_insured = models.IntegerField(default=0.0)
    suminsured_range = IntegerRangeField(default=(0, 300000), db_index=True)
    age_range = IntegerRangeField(default=(0, 100), db_index=True)
    adults = models.IntegerField(null=True, blank=True, db_index=True)
    childrens = models.IntegerField(null=True, blank=True, db_index=True)
    citytier = models.CharField(
        max_length=256, null=True, blank=True)
    base_premium = models.FloatField(default=Constants.DEFAULT_BASE_PREMIUM)
    gst = models.FloatField(default=Constants.DEFAULT_GST)
    commission = models.FloatField(default=0.0)
    premium = GenericRelation(
        'sales.quote', related_query_name='healthinsurance',
        object_id_field='premium_id')
    ignore = models.BooleanField(default=False)

    def get_details(self):
        return {
            'sum_insured': self.sum_insured,
            'amount': self.amount,
            'commision': self.commission_amount
        }

    @cached_property
    def commission_amount(self):
        company = self.product_variant.company_category.company
        category = self.product_variant.company_category.category
        return self.amount * (
            self.commission + company.commission + category.commission)

    @cached_property
    def amount(self):
        return round((self.gst * self.base_premium) + self.base_premium, 2)

    def __str__(self):
        return '%s | %s' % (self.sum_insured, self.age_range)
