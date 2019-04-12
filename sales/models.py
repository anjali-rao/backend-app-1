# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import (
    constants, get_choices, genrate_random_string)

from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.utils.functional import cached_property
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation)


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
            self.premium.amount,
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


class Application(BaseModel):
    reference_no = models.CharField(max_length=10, unique=True)
    application_type = models.CharField(
        max_length=32, choices=get_choices(constants.APPLICATION_TYPES))
    quote = models.OneToOneField('sales.Quote', on_delete=models.CASCADE)
    address = models.ForeignKey(
        'users.Address', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(
        max_length=32, choices=constants.STATUS_CHOICES, default='pending')
    people_listed = models.IntegerField(default=0)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True)
    insurance_id = models.PositiveIntegerField(null=True, blank=True)
    insurance = GenericForeignKey('content_type', 'insurance_id')

    def save(self, *args, **kwargs):
        if not self.__class__.objects.filter(pk=self.id).exists():
            self.generate_reference_no()
            self.application_type = self.company_category.category.name.lower().replace(' ', '_') # noqaas
        super(Application, self).save(*args, **kwargs)

    def generate_reference_no(self):
        self.reference_no = genrate_random_string(10)
        if self.__class__.objects.filter(
                reference_no=self.reference_no).exists():
            while self.__class__.objects.filter(
                    reference_no=self.reference_no).exists():
                self.reference_no = genrate_random_string(10)

    @cached_property
    def active_members(self):
        return self.member_set.filter(ignore=False)

    @cached_property
    def inactive_members(self):
        return self.member_set.filter(ignore=True)

    @cached_property
    def company_category(self):
        return self.quote.premium.product_variant.company_category

    def __str__(self):
        return '%s - %s - %s' % (
            self.reference_no, self.application_type,
            self.company_category.company.name)


class Member(BaseModel):
    application = models.ForeignKey(
        'sales.Application', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=256)
    dob = models.DateField()
    gender = models.CharField(
        choices=get_choices(constants.GENDER), max_length=16)
    occupation = models.CharField(
        choices=get_choices(constants.OCCUPATION_CHOICES), max_length=32)
    ignore = models.BooleanField(default=False)

    @property
    def age(self):
        days = (now().date() - self.dob).days
        return '%s years and %s months' % ((days % 365) / 30, days / 365)


class HealthInsurance(BaseModel):
    application = GenericRelation(
        Application, related_query_name='health_insurance',
        object_id_field='insurance_id')


class TravelInsurance(BaseModel):
    application = GenericRelation(
        Application, related_query_name='travel_insurance',
        object_id_field='insurance_id')


class Policy(BaseModel):
    application = models.OneToOneField(
        'sales.Application', on_delete=models.CASCADE)
    contact = models.ForeignKey('crm.Contact', on_delete=models.CASCADE)
    policy_data = JSONField()


@receiver(post_save, sender=Application, dispatch_uid="action%s" % str(now()))
def application_post_save(sender, instance, created, **kwargs):
    if created:
        content_type = ContentType.objects.get(
            model=instance.application_type.replace('_', ''),
            app_label='sales')
        instance.content_type_id = content_type.id
        instance.insurance_id = content_type.model_class().objects.create().id
        instance.save()
        Quote.objects.filter(lead_id=instance.quote.lead.id).exclude(
            id=instance.quote_id).update(status='rejected')
        instance.quote.status = 'accepted'
        instance.quote.save()
