# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import (
    constants, get_choices, genrate_random_string)

from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.utils.functional import cached_property
from django.db.models.signals import post_save
from django.db import IntegrityError
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
                    company_category.company.website or '-'
                )
            }
        ]


class Application(BaseModel):
    reference_no = models.CharField(max_length=10, unique=True, db_index=True)
    application_type = models.CharField(
        max_length=32, choices=get_choices(constants.APPLICATION_TYPES))
    quote = models.OneToOneField('sales.Quote', on_delete=models.CASCADE)
    address = models.ForeignKey(
        'users.Address', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(
        max_length=32, choices=constants.STATUS_CHOICES, default='pending')
    previous_policy = models.BooleanField(default=False)
    name_of_insurer = models.CharField(blank=True, max_length=128)
    terms_and_conditions = models.BooleanField(null=True)

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

    def add_default_members(self):
        lead = self.quote.lead
        today = now()
        members = list()

        def add(gender, relation, dob):
            return Member(
                application_id=self.id, dob=dob, relation=relation,
                gender=gender
            )
        for member, age in lead.family.items():
            member = member.split('_')[0]
            gender = lead.gender if member == 'self' else 'male'
            if member == 'spouse':
                gender = 'male' if lead.gender == 'female' else 'female'
            elif member == 'mother':
                gender = 'female'
            elif member in ['son', 'daughter']:
                while age > 0:
                    members.append(add(
                        'male' if member == 'son' else 'female'), member)
                    age -= 1
                continue
            instance = add(gender, member, '%s-%s-%s' % (
                today.year - int(age), today.month, today.day))
            members.append(instance)
        Member.objects.bulk_create(members)

    @cached_property
    def active_members(self):
        return self.member_set.filter(ignore=False)

    @cached_property
    def inactive_members(self):
        return self.member_set.exclude(ignore=False)

    @cached_property
    def company_category(self):
        return self.quote.premium.product_variant.company_category

    @cached_property
    def people_listed(self):
        return self.active_members.count()

    def __str__(self):
        return '%s - %s - %s' % (
            self.reference_no, self.application_type,
            self.company_category.company.name)


class Member(BaseModel):
    application = models.ForeignKey(
        'sales.Application', on_delete=models.CASCADE)
    relation = models.CharField(
        max_length=128, choices=get_choices(constants.RELATION_CHOICES),
        db_index=True)
    first_name = models.CharField(max_length=128, blank=True)
    middle_name = models.CharField(max_length=128, blank=True)
    last_name = models.CharField(max_length=128, blank=True)
    dob = models.DateField(blank=True)
    gender = models.CharField(
        choices=get_choices(constants.GENDER), max_length=16)
    occupation = models.CharField(
        choices=get_choices(constants.OCCUPATION_CHOICES), max_length=32
    )
    height = models.FloatField(default=0.0)
    weight = models.FloatField(default=0.0)
    ignore = models.BooleanField(default=None, db_index=True)

    def save(self, *ar, **kw):
        try:
            self.__class__.objects.get(pk=self.id)
        except self.__class__.DoesNotExist:
            if self.relation not in [
                'son', 'daughter'] and self.__class__.objects.filter(
                    relation=self.relation).exists():
                raise IntegrityError(
                    '%s relation already exists.' % self.relation)
        super(Member, self).save(*ar, **kw)

    def get_full_name(self):
        name = '%s %s %s' % (self.first_name, self.middle_name, self.last_name)
        return name.strip()

    @property
    def age(self):
        return '%s Years' % int((
            now().today().date() - self.dob).days / 365.2425)

    @property
    def height_foot(self):
        return int(self.height / 30.48)

    @property
    def height_inches(self):
        return round((self.height - self.height_foot * 30.48) / 2.54, 2)


class Nominee(BaseModel):
    application = models.ForeignKey(
        'sales.Application', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=128)
    middle_name = models.CharField(max_length=128, blank=True)
    last_name = models.CharField(max_length=128)
    phone_no = models.CharField(max_length=10)
    ignore = models.BooleanField(default=False)

    def save(self, *ar, **kw):
        existing_nominee = self.__class__.objects.filter(pk=self.id)
        if existing_nominee.exists():
            existing_nominee.update(ignore=True)
        super(Nominee, self).save(*ar, **kw)


class Insurance(BaseModel):

    class Meta:
        abstract = True

    application = models.OneToOneField(
        'sales.Application', on_delete=models.CASCADE, null=True)


class HealthInsurance(Insurance):

    gastrointestinal_disease = models.BooleanField(
        default=False, help_text=constants.GASTROINTESTINAL_DISEASE)
    neuronal_diseases = models.BooleanField(
        default=False, help_text=constants.NEURONAL_DISEASES)
    alcohol_consumption = models.BooleanField(
        default=False, help_text=constants.ALCOHOL_CONSUMPTION)
    tabacco_consumption = models.BooleanField(
        default=False, help_text=constants.TABBACO_CONSUMPTION)
    cigarette_consumption = models.BooleanField(
        default=False, help_text=constants.CIGARETTE_CONSUMPTION)
    previous_claim = models.BooleanField(
        default=False, help_text=constants.PREVIOUS_CLAIM)
    proposal_terms = models.BooleanField(
        default=False, help_text=constants.PROPOSAL_TERMS)
    existing_policy = models.BooleanField(
        default=False, help_text=constants.EXISTING_POLICY)
    oncology_disease = models.BooleanField(
        default=False, help_text=constants.ONCOLOGY_DISEASE)
    respiratory_diseases = models.BooleanField(
        default=False, help_text=constants.RESPIRATORY_DISEASES)
    cardiovascular_disease = models.BooleanField(
        default=False, help_text=constants.CARDIOVASCULAR_DISEASE)
    ent_diseases = models.BooleanField(
        default=False, help_text=constants.ENT_DISEASE)
    blood_diseases = models.BooleanField(
        default=False, help_text=constants.BLOOD_DISODER)

#
# class TravelInsurance(BaseInsurance):
#


class Policy(BaseModel):
    application = models.OneToOneField(
        'sales.Application', on_delete=models.CASCADE)
    contact = models.ForeignKey('crm.Contact', on_delete=models.CASCADE)
    policy_data = JSONField()


@receiver(post_save, sender=Application, dispatch_uid="action%s" % str(now()))
def application_post_save(sender, instance, created, **kwargs):
    if created:
        ContentType.objects.get(
            model=instance.application_type.replace('_', ''), app_label='sales'
        ).model_class().objects.create(application_id=instance.id)
        Quote.objects.filter(lead_id=instance.quote.lead.id).exclude(
            id=instance.quote_id).update(status='rejected')
        instance.quote.status = 'accepted'
        instance.add_default_members()
