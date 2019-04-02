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
    recommendation_score = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('lead', 'premium',)

    @classmethod
    def get_compareable_features(cls, *quotes_ids):
        features = list()
        for quote_id in quotes_ids:
            features.extend(
                cls.objects.get(id=quote_id).quotefeature_set.annotate(
                    name=models.F('feature__feature_master__name')
                ).values_list('name', flat=True))
        return set(features)

    def get_feature_details(self):
        features = []
        for feature in self.quotefeature_set.annotate(
            name=models.F('feature__feature_master__name'),
            description=models.F('feature__feature_master__long_description'),
            short_text=models.F('feature__short_description')
        ).values('name', 'score', 'description', 'short_text'):
            features.append({
                'name': feature['name'],
                'description': feature['description'],
                'short_text': feature['short_text'],
                'score': feature['score']
            })
        return features


class QuoteFeature(BaseModel):
    quote = models.ForeignKey('sales.Quote', on_delete=models.CASCADE)
    feature = models.ForeignKey('product.feature', on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        super(QuoteFeature, self).save(*args, **kwargs)
        self.quote.recommendation_score += float(
            self.feature.rating * self.score)
        self.quote.save()


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
    application_type = models.CharField(
        max_length=32, choices=get_choices(constants.APPLICATION_TYPES))
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

    def assignInsurance(self):
        # to DOs
        if self.application_type == 'health_insurance':
            HealthInsurance.objects.create()

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


class HealthInsurance(BaseModel):
    application = models.OneToOneField('sales.Application')
