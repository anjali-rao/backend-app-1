# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.model import BaseModel, models
from utils import constants, get_choices


class Category(BaseModel):
    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True)
    logo = models.ImageField(
        upload_to=constants.CATEGORY_UPLOAD_PATH,
        default=constants.DEFAULT_LOGO)
    hexa_code = models.CharField(
        max_length=8, default=constants.DEFAULT_HEXA_CODE)

    def __str__(self):
        return self.name


class Company(BaseModel):
    name = models.CharField(max_length=128)
    short_name = models.CharField(max_length=128)
    categories = models.ManyToManyField('product.Category')
    logo = models.ImageField(
        upload_to=constants.COMPANY_UPLOAD_PATH,
        default=constants.DEFAULT_LOGO)
    hexa_code = models.CharField(
        max_length=8, default=constants.DEFAULT_HEXA_CODE)
    website = models.URLField(null=True, blank=True)
    spoc = models.TextField(null=True, blank=True)
    toll_free_number = models.CharField(max_length=50, null=True, blank=True)
    long_description = models.TextField(null=True, blank=True)
    small_description = models.TextField(null=True, blank=True)

    def __str__(self):
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

    class Meta:
        unique_together = ('category', 'company')

    def __str__(self):
        return '%s - %s' % (self.category.name, self.company.name)


class ProductVariant(BaseModel):
    company_category = models.ForeignKey('product.CompanyCategory')
    name = models.CharField(max_length=256, default="")
    parent_product = models.CharField(max_length=128, default='GoPlannr')
    feature_variant = models.CharField(max_length=256, default='base')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True)
    adult = models.IntegerField(default=0)
    children = models.IntegerField(default=0)
    city = models.CharField(max_length=64, null=True, blank=True)
    chronic = models.BooleanField(default=True)

    def get_product_details(self):
        from goplannr.settings import BASE_HOST
        return {
            'name': self.parent_product,
            'company': self.company_category.company.name,
            'logo': BASE_HOST + self.company_category.company.logo.url
        }

    def get_basic_details(self):
        return {
            'toll_free_number': self.company_category.company.toll_free_number,
            'brochure': self.get_help_file('SALES BROCHURES'),
            'claim_form': self.get_help_file('CLAIM FORMS')
        }

    def get_help_file(self, file_type):
        from content.models import HelpFile
        helpfile = HelpFile.objects.filter(
            category=self.company_category.category.name,
            file_type=file_type).last()
        if not helpfile:
            helpfile = HelpFile.objects.filter(
                category='ALL', file_type=file_type).last()
        return helpfile.file.url if helpfile else ''

    class Meta:
        unique_together = ('company_category', 'name')

    def __str__(self):
        return self.name


class CustomerSegment(BaseModel):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class FeatureMaster(BaseModel):
    category = models.ForeignKey('product.Category')
    name = models.CharField(max_length=127, default="")
    feature_type = models.CharField(
        max_length=32, default='Others',
        choices=get_choices(constants.FEATURE_TYPES))
    description = models.TextField(default="")

    def __str__(self):
        return "%s - %s" % (
            self.name, self.category.name)


class Feature(BaseModel):
    feature_master = models.ForeignKey('product.FeatureMaster')
    product_variant = models.ForeignKey('product.ProductVariant')
    short_description = models.CharField(max_length=256)
    rating = models.IntegerField(default=0.0)
    long_description = models.CharField(max_length=256)

    def __str__(self):
        return "%s - %s" % (
            self.product_variant.name, self.feature_master.name)


class FeatureCustomerSegmentScore(BaseModel):
    feature = models.ForeignKey(Feature)
    customer_segment = models.ForeignKey(CustomerSegment)
    score = models.FloatField(default=0.0)


class SumInsuredMaster(models.Model):
    text = models.CharField(max_length=64)
    number = models.IntegerField()

    def __str__(self):
        return self.text


class DeductibleMaster(models.Model):
    text = models.CharField(max_length=100)
    number = models.IntegerField()

    def __str__(self):
        return self.text


class Premium(BaseModel):
    product_variant = models.ForeignKey('product.ProductVariant')
    sum_insured = models.ForeignKey('product.SumInsuredMaster')
    min_age = models.IntegerField(default=0)
    max_age = models.IntegerField(default=0)
    deductible = models.ForeignKey(
        'product.DeductibleMaster', null=True, blank=True)
    base_premium = models.FloatField(default=constants.DEFAULT_BASE_PREMIUM)
    gst = models.FloatField(default=constants.DEFAULT_GST)
    commission = models.FloatField(default=constants.DEFAULT_COMMISSION)

    def get_details(self):
        return {
            'sum_insured': self.sum_insured.number,
            'amount': self.amount,
            'commision': self.get_commission_amount()
        }

    def get_commission_amount(self):
        return self.amount * self.commission

    @property
    def amount(self):
        return (
            self.gst * self.base_premium
        ) + self.base_premium + self.commission
