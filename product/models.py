# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.model import BaseModel, models
from utils import constants


class Category(BaseModel):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class Company(BaseModel):
    name = models.CharField(max_length=128)
    short_name = models.CharField(max_length=64)
    categories = models.ManyToManyField('product.Category')
    logo = models.ImageField(upload_to=constants.COMPANY_UPLOAD_PATH)
    hexa_code = models.CharField(max_length=8)
    short_name = models.CharField(max_length=128)
    website = models.URLField(null=True, blank=True)
    spoc = models.TextField(null=True, blank=True)
    toll_free_number = models.CharField(max_length=50, null=True, blank=True)
    long_description = models.TextField(null=True, blank=True)
    small_description = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class CompanyDetails(BaseModel):
    company = models.OneToOneField('product.Company')
    fact_file = models.TextField(null=True, blank=True)
    joint_venture = models.TextField(null=True, blank=True)
    formation_year = models.CharField(max_length=4, null=True, blank=True)
    market_share = models.TextField(null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)


class CompanyCategory(BaseModel):
    category = models.ForeignKey('product.Category')
    company = models.ForeignKey('product.Company')
    claim_settlement = models.TextField(null=True, blank=True)
    offer_flag = models.BooleanField(default=False)
    # network = models.ManyToManyField(NetworkHospital)

    class Meta:
        unique_together = ('category', 'company')


class ProductVariant(BaseModel):
    company_category = models.ForeignKey('product.CompanyCategory')
    name = models.CharField(max_length=128, default="")
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True)
    adult = models.IntegerField(default=0)
    children = models.IntegerField(default=0)
    city = models.CharField(max_length=64)
    chronic = models.BooleanField(default=True)

    def get_product_details(self):
        return {
            'name': self.name,
            'company': self.company_category.company.name,
            'category': self.company_category.category.name
        }

    class Meta:
        unique_together = ('company_category', 'name')

    def __unicode__(self):
        return self.name


class CustomerSegment(BaseModel):
    name = models.CharField(max_length=128)

    def __unicode__(self):
        return self.name


class FeatureMaster(BaseModel):
    category = models.ForeignKey('product.Category')
    name = models.CharField(max_length=127, default="")
    description = models.TextField(default="")

    def __unicode__(self):
        return "%s - %s" % (
            self.name, self.category.name)


class Feature(BaseModel):
    feature_master = models.ForeignKey('product.FeatureMaster')
    product_variant = models.ForeignKey('product.ProductVariant')
    short_description = models.CharField(max_length=256)
    rating = models.IntegerField(default=0.0)
    long_description = models.CharField(max_length=256)

    def __unicode__(self):
        return "%s - %s" % (
            self.product_variant.name, self.feature_master.name)


class FeatureCustomerSegmentScore(BaseModel):
    feature = models.ForeignKey(Feature)
    customer_segment = models.ForeignKey(CustomerSegment)
    score = models.FloatField(default=0.0)


class SumInsuredMaster(models.Model):
    text = models.CharField(max_length=64)
    number = models.IntegerField()

    def __unicode__(self):
        return self.text


class DeductibleMaster(models.Model):
    text = models.CharField(max_length=100)
    number = models.IntegerField()

    def __unicode__(self):
        return self.text


class Premium(BaseModel):
    product_variant = models.ForeignKey('product.ProductVariant')
    sum_insured = models.ForeignKey('product.SumInsuredMaster')
    amount = models.IntegerField(default=0, blank=False, null=False)
    min_age = models.IntegerField(default=0)
    max_age = models.IntegerField(default=0)
    deductible = models.ForeignKey('product.DeductibleMaster')
    base_premium = models.FloatField(default=constants.DEFAULT_BASE_PREMIUM)
    gst = models.FloatField(default=constants.DEFAULT_GST)
    commission = models.FloatField(default=constants.DEFAULT_COMMISSION)

    def get_details(self):
        return {
            'sum_insured': self.sum_insured.number,
            'amount': self.amount,
            'commision': self.commission
        }
