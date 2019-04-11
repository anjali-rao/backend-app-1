# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import (
    constants, get_choices, get_kyc_upload_path, genrate_random_string)

from django.contrib.postgres.fields import JSONField
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now


class Quote(BaseModel):
    lead = models.ForeignKey('crm.Lead', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=16, choices=constants.STATUS_CHOICES,
        default='pending')
    premium = models.ForeignKey(
        'product.Premium', null=True, blank=True, on_delete=models.CASCADE)
    recommendation_score = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('lead', 'premium',)

    def __str__(self):
        return '%s - %s' % (
            self.lead.final_score,
            self.premium.product_variant.company_category.company.name)

    def get_feature_details(self):
        return self.premium.product_variant.feature_set.values(
            'feature_master__name', 'short_description',
            'feature_master__long_description'
        ).order_by('feature_master__order')

    def get_faq(self):
        company_category = self.premium.product_variant.company_category
        return [
            {
                'question': 'Claim settlement ratio',
                'answer': company_category.claim_settlement
            },
            {
                'question': 'Company details',
                'answer': 'Name: %s\nWebsite: %s' % (
                    company_category.company.name,
                    company_category.company.website
                )
            }
        ]


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
    quote = models.OneToOneField('sales.Quote', on_delete=models.CASCADE)
    address = models.ForeignKey(
        'users.Address', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(
        max_length=32, choices=constants.STATUS_CHOICES, default='pending')
    people_listed = models.IntegerField(default=0)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    insurance_id = models.PositiveIntegerField()
    insurance = GenericForeignKey('content_type', 'insurance_id')

    def save(self, *args, **kwargs):
        try:
            self.__class__.objects.get(pk=self.id)
        except Application.DoesNotExist:
            self.generate_reference_no()
            self.assign_insurance()
        super(Application, self).save(*args, **kwargs)

    def assign_insurance(self):
        category = self.quote.premium.product_variant.company_category.category.name # noqa
        if category == 'Health Insurance':
            self.application_type = 'health_insurance'
        elif category == 'Travel Insurance': # noqa
            self.application_type = 'travel_insurance'

    def generate_reference_no(self):
        self.reference_no = 'GoPlannr%s' % genrate_random_string(10)
        if self.__class__.objects.filter(
                reference_no=self.reference_no).exists():
            while self.__class__.objects.filter(
                    reference_no=self.reference_no).exists():
                self.reference_no = 'GoPlannr%s' % genrate_random_string(10)


class HealthInsurance(BaseModel):
    application = GenericRelation(
        Application, related_query_name='health_insurance',
        object_id_field='insurance_id')


class TravelInsurance(BaseModel):
    application = GenericRelation(
        Application, related_query_name='travel_insurance',
        object_id_field='insurance_id')


class KYCDocuments(BaseModel):
    client = models.ForeignKey('sales.Client', on_delete=models.CASCADE)
    number = models.CharField(max_length=64)
    doc_type = models.CharField(
        choices=get_choices(constants.KYC_DOC_TYPES), max_length=16)
    file = models.FileField(upload_to=get_kyc_upload_path)


class Policy(BaseModel):
    application = models.OneToOneField(
        'sales.Application', on_delete=models.CASCADE)
    contact = models.ForeignKey('crm.Contact', on_delete=models.CASCADE)
    client = models.ForeignKey('sales.Client', on_delete=models.CASCADE)
    policy_data = JSONField()


@receiver(post_save, sender=Application, dispatch_uid="action%s" % str(now()))
def user_post_save(sender, instance, created, **kwargs):
    if created:
        pass
