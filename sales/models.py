# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.model import BaseModel, models
from utils import (
    constants, get_choices, get_kyc_upload_path, genrate_random_string)

from django.contrib.postgres.fields import JSONField


class Quote(BaseModel):
    lead = models.ForeignKey('crm.Lead')
    status = models.CharField(
        max_length=16, choices=constants.STATUS_CHOICES,
        default='pending')
    premium = models.ForeignKey('product.Premium', null=True, blank=True)

    @property
    def recommendation_score(self):
        return QuoteFeature.objects.filter(quote_id=self.id).aggregate(
            s=models.Sum('feature_recommendation_score'))['s']

    class Meta:
        unique_together = ('lead', 'premium',)


class QuoteFeature(BaseModel):
    quote = models.ForeignKey('sales.Quote', on_delete=models.CASCADE)
    feature = models.ForeignKey('product.feature', on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    feature_recommendation_score = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        self.feature_recommendation_score = self.feature.rating * self.score
        super(QuoteFeature, self).save(*args, **kwargs)


class KYCDocuments(BaseModel):
    client = models.ForeignKey('sales.Client')
    number = models.CharField(max_length=64)
    doc_type = models.CharField(
        choices=get_choices(constants.KYC_DOC_TYPES), max_length=16)
    file = models.FileField(upload_to=get_kyc_upload_path)


class Client(BaseModel):
    document_number = models.CharField(max_length=32)
    first_name = models.CharField(max_length=32)
    middle_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    dob = models.DateField()
    email = models.EmailField()
    contact_no = models.CharField(max_length=10)
    alternate_no = models.CharField(max_length=10)

    def update_details(self, data):
        self.first_name = data['first_name']
        self.last_name = data['last_name']
        self.middle_name = data['middle_name']
        self.dob = data['dob']
        self.email = data['email']
        self.contact_no = data['contact_no']
        self.alternate_no = data['alternate_no']
        self.save()


class Application(BaseModel):
    reference_no = models.CharField(max_length=15, unique=True)
    quote = models.OneToOneField('sales.Quote')
    address = models.ForeignKey('users.Address')
    status = models.CharField(
        max_length=32, choices=constants.STATUS_CHOICES, default='pending')
    people_listed = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        try:
            self.__class__.objects.get(pk=self.id)
        except Application.DoesNotExist:
            self.generate_reference_no()
        super(Application, self).save(*args, **kwargs)

    def generate_reference_no(self):
        self.reference_no = 'GoPlannr%s' % genrate_random_string(10)
        if self.__class__.objects.filter(
                reference_no=self.reference_no).exists():
            while self.__class__.objects.filter(
                    reference_no=self.reference_no).exists():
                self.reference_no = 'GoPlannr%s' % genrate_random_string(10)


class Policy(BaseModel):
    application = models.OneToOneField('sales.Application')
    contact = models.ForeignKey('crm.Contact')
    client = models.ForeignKey(Client)
    policy_data = JSONField()


# class InsuranceApplication(BaseModel):
#     quote = models.OneToOneField(Quote)
#     first_name = models.CharField(max_length=127, default="")
#     middle_name = models.CharField(max_length=127,null=True,blank=True)
#     last_name = models.CharField(max_length=127, default="")
#     date_of_birth = models.CharField(max_length=127, default="")
#     email = models.CharField(max_length=127, default="")
#     pan_number = models.CharField(max_length=127, default="")
#     contact_no = models.CharField(max_length=127, default="")
#     contact_no2 = models.CharField(max_length=127,null=True,blank=True)
#     address = models.TextField(null=True,blank=True)
#     appartment_no = models.CharField(max_length=127,null=True,blank=True)
#     city = models.CharField(max_length=127,null=True,blank=True)
#     zip_code = models.CharField(max_length=127,null=True,blank=True)
#     country = models.CharField(max_length=127,null=True,blank=True)
#     no_of_people_listed = models.IntegerField(null=True,blank=True)


# class HealthApplication(BaseModel):
#     quote = models.OneToOneField(Quote)
