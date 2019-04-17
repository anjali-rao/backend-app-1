# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.postgres.fields import JSONField

from utils.models import BaseModel, models
from utils import constants, get_choices, get_kyc_upload_path

from sales.models import Quote
from product.models import (
    Premium, FeatureCustomerSegmentScore, Feature
)
import math


class Lead(BaseModel):
    user = models.ForeignKey('users.user', on_delete=models.CASCADE)
    contact = models.ForeignKey(
        'crm.Contact', null=True, blank=True, on_delete=models.CASCADE)
    category = models.ForeignKey('product.Category', on_delete=models.CASCADE)
    customer_segment = models.ForeignKey(
        'product.CustomerSegment', null=True, blank=True,
        on_delete=models.CASCADE)
    campaign = models.ForeignKey(
        'users.Campaign', null=True, blank=True, on_delete=models.CASCADE)
    amount = models.FloatField(default=0.0)
    status = models.CharField(
        choices=constants.LEAD_STATUS_CHOICES, default='fresh', max_length=32)
    stage = models.CharField(
        choices=constants.LEAD_STAGE_CHOICES, default='new', max_length=32)
    # notes = models.ManyToManyField(Note)
    final_score = models.FloatField(default=0.0, db_index=True)
    effective_age = models.IntegerField(default=0)
    tax_saving = models.FloatField(default=0.30)
    wellness_rewards = models.FloatField(default=0.10)
    health_checkups = models.FloatField(default=0.0)
    pincode = models.CharField(max_length=6, null=True)
    adults = models.IntegerField(default=0)
    gender = models.CharField(max_length=12)
    childrens = models.IntegerField(default=0)
    family = JSONField(default=dict)

    def save(self, *args, **kwargs):
        try:
            current = self.__class__.objects.get(pk=self.id)
            if self.final_score != current.final_score:
                self.refresh_quote_data()
        except Lead.DoesNotExist:
            self.parse_family_json()
        super(Lead, self).save(*args, **kwargs)

    def parse_family_json(self):
        if 'daughter_total' in self.family:
            self.childrens += self.family['daughter_total']
            self.family.pop('daughter_total')
        if 'son_total' in self.family:
            self.childrens += self.family['son_total']
            self.family.pop('son_total')
        ages = self.family.values()
        self.effective_age = int(max(ages))
        self.adults = len(ages)

    def calculate_final_score(self):
        from questionnaire.models import Response
        self.final_score = math.ceil(
            Response.objects.select_related('answer').filter(
                lead_id=self.id).aggregate(
                s=models.Sum('answer__score'))['s'])
        if self.final_score <= 3:
            self.final_score = 3
        elif self.final_score <= 5:
            self.final_score = 5
        elif self.final_score <= 7:
            self.final_score = 7
        elif self.final_score <= 10:
            self.final_score = 10
        elif self.final_score <= 20:
            self.final_score = 20
        else:
            self.final_score = 50
        self.final_score *= 100000
        self.customer_segment_id = self.get_customer_segment().id
        self.save()

    def get_premiums(self):
        # product_variant__citytier=self.citytier,
        queryset = Premium.objects.select_related(
            'product_variant'
        ).filter(
            product_variant__company_category__category_id=self.category_id,
            sum_insured=self.final_score, adults=self.adults,
        )
        if self.childrens <= 4:
            queryset = queryset.filter(childrens=self.childrens)
        return queryset.filter(
            age_range__contains=(self.effective_age + 1)) or queryset[:7]

    def refresh_quote_data(self):
        quotes = self.get_quotes()
        if quotes.exists():
            for quote in quotes:
                quote.delete()
        for premium in self.get_premiums():
            feature_masters = premium.product_variant.feature_set.values_list(
                'feature_master_id', flat=True)
            quote = Quote.objects.create(
                lead_id=self.id, premium_id=premium.id)
            changed_made = False
            for feature_master_id in feature_masters:
                feature_score = FeatureCustomerSegmentScore.objects.only(
                    'score', 'feature_master_id').filter(
                        feature_master_id=feature_master_id,
                        customer_segment_id=self.customer_segment.id).last()
                if feature_score is not None:
                    if not changed_made:
                        changed_made = False
                    quote.recommendation_score += float(Feature.objects.filter(
                        feature_master_id=feature_master_id).aggregate(
                        s=models.Sum('rating'))['s'] * feature_score.score)
            if changed_made:
                quote.save()

    def get_customer_segment(self):
        from product.models import CustomerSegment
        from questionnaire.models import Response
        responses = Response.objects.select_related(
            'answer', 'question').filter(lead_id=self.id)
        segment_name = 'young_adult'
        if 'self_age' in self.family:
            age = int(self.family['self_age'])
            if age <= 35:
                segment_name = 'young_adult'
            if any(x in self.family for x in ['mother_age', 'father_age']) and age < 35: # noqa
                segment_name = 'young_adult_with_dependent_parents'
            if age > 50:
                segment_name = 'senior_citizens'
            if 'spouse_age' in self.family:
                if age < 35:
                    segment_name = 'young_couple'
                if age > 50:
                    segment_name = 'senior_citizens'
                if self.family.get('kid', 0) >= 1 and age < 40:
                    segment_name = 'young_family'
                if self.family.get('kid', 0) >= 1 and age < 60:
                    segment_name = 'middle_aged_family'
            emp_resp = responses.filter(question__title='Occupation')
            if emp_resp.exists() and emp_resp.filter(
                    answer__answer='Self Employed or Business').exists():
                segment_name = 'self_employed'
        if self.effective_age < 40 and self.childrens >= 1:
            segment_name = 'young_family'
        elif self.effective_age <= 35 and self.adults == 1:
            segment_name = 'young_adult'
        elif self.effective_age <= 35 and self.adults == 2:
            segment_name = 'young_couple'
        elif self.effective_age < 60 and self.childrens >= 1:
            segment_name = 'middle_aged_family'
        elif self.effective_age >= 50:
            segment_name = 'senior_citizens'
        return CustomerSegment.objects.only('id').get(name=segment_name)

    def get_quotes(self):
        return self.quote_set.all().order_by('-recommendation_score')

    def get_recommendated_quotes(self):
        return self.get_quotes()[:5]

    def update_fields(self, **kw):
        updated = False
        for field in kw.keys():
            setattr(self, field, kw[field])
            if not updated:
                updated = True
        if updated:
            self.save()

    @property
    def city(self):
        from users.models import Pincode
        pincodes = Pincode.objects.filter(pincode=self.pincode)
        if pincodes.exists():
            return pincodes.get().city

    @property
    def citytier(self):
        if self.city in constants.TIER_1_CITIES:
            return 1
        elif self.city in constants.TIER_2_CITIES:
            return 2
        return 3

    def __str__(self):
        return "%s - %s" % (
            self.contact.first_name if self.contact else 'Contact',
            self.category.name)


class Contact(BaseModel):
    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True)
    address = models.ForeignKey(
        'users.Address', null=True, blank=True, on_delete=models.CASCADE)
    phone_no = models.CharField(max_length=10, null=True, blank=True)
    first_name = models.CharField(max_length=32, blank=True)
    middle_name = models.CharField(max_length=32, blank=True)
    last_name = models.CharField(max_length=32, blank=True)
    email = models.EmailField(max_length=64, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    occupation = models.CharField(
        choices=get_choices(constants.OCCUPATION_CHOICES), null=True,
        default=constants.OCCUPATION_DEFAULT_CHOICE, blank=True, max_length=32)
    marital_status = models.CharField(
        choices=get_choices(
            constants.MARITAL_STATUS), max_length=32, null=True, blank=True)
    annual_income = models.FloatField(default=0.0)
    is_client = models.BooleanField(default=False)

    def __str__(self):
        full_name = self.get_full_name()
        return '%s - %s' % ((
            full_name if full_name else 'Parent'
        ), self.phone_no)

    def update_fields(self, **kw):
        updated = False
        for field in kw.keys():
            setattr(self, field, kw[field])
            if not updated:
                updated = True
        if updated:
            self.save()

    def is_kyc_required(self):
        try:
            if not self.kycdocument.file:
                return False
        except Exception:
            pass
        return True

    def get_full_name(self):
        full_name = '%s %s %s' % (
            self.first_name, self.middle_name, self.last_name)
        return full_name.strip()


class KYCDocument(BaseModel):
    contact = models.OneToOneField('crm.Contact', on_delete=models.CASCADE)
    docunent_number = models.CharField(max_length=64)
    document_type = models.CharField(
        choices=get_choices(constants.KYC_DOC_TYPES), max_length=16)
    file = models.FileField(upload_to=get_kyc_upload_path)
