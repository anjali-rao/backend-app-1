# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.postgres.fields import JSONField

from utils.model import BaseModel, models
from utils import constants


class Category(BaseModel):
    name = models.CharField(max_length=128)
    short_name = models.CharField(max_length=40)
    logo = models.ImageField(upload_to=constants.CATEGORY_UPLOAD_PATH)
    description = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class Company(BaseModel):
    name = models.CharField(max_length=256)
    enterprise = models.ForeignKey('users.Enterprise')
    categories = models.ManyToManyField(Category)
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
    company = models.OneToOneField(Company)
    fact_file = models.TextField(null=True, blank=True)
    joint_venture = models.TextField(null=True, blank=True)
    formation_year = models.CharField(max_length=4, null=True, blank=True)
    market_share = models.TextField(null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)


class CompanyCategory(BaseModel):
    category = models.ForeignKey(Category)
    company = models.ForeignKey(Company)
    claim_settlement = models.TextField(null=True, blank=True)
    offer_flag = models.BooleanField(default=False)
    # network = models.ManyToManyField(NetworkHospital)

    class Meta:
        unique_together = ('category', 'company')


class ProductVariant(BaseModel):
    company_category = models.ForeignKey(CompanyCategory)
    name = models.CharField(max_length=127, default="")
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = ('company_category', 'name')

    def __unicode__(self):
        return self.name


class CustomerSegment(BaseModel):
    name = models.CharField(max_length=128)

    def __unicode__(self):
        return self.name


class FeatureMaster(BaseModel):
    category = models.ForeignKey(Category)
    name = models.CharField(max_length=127, default="")
    description = models.TextField(default="")

    def __unicode__(self):
        return "%s - %s" % (
            self.name, self.category.name)


class Feature(BaseModel):
    feature_master = models.ForeignKey(FeatureMaster)
    product_variant = models.ForeignKey(ProductVariant)

    def __unicode__(self):
        return "%s - %s" % (
            self.product_variant.name, self.feature_master.name)


class FeatureCustomerSegmentScore(BaseModel):
    feature = models.ForeignKey(Feature)
    customer_segment = models.ForeignKey(CustomerSegment)
    score = models.FloatField(null=True, blank=True, default=None)


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
    product_variant = models.ForeignKey(ProductVariant)
    sum_insured = models.ForeignKey(SumInsuredMaster)
    min_age = models.IntegerField(default=0)
    max_age = models.IntegerField(default=0)
    deductible = models.ForeignKey(DeductibleMaster)
    base_premium = models.FloatField(default=constants.DEFAULT_BASE_PREMIUM)
    gst = models.FloatField(default=constants.DEFAULT_GST)
    commission = models.FloatField(default=constants.DEFAULT_COMMISSION)


class Questionnaire(BaseModel):
    category = models.ForeignKey(Category)
    question = models.TextField()
    answer_score = JSONField()


class QuestionAnswer(BaseModel):
    question = models.ForeignKey(Questionnaire)
    # lead = models.ForeignKey(Lead)
    answer = models.TextField()
    score = models.FloatField()
