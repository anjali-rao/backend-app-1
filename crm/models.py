# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.postgres.fields import JSONField

from utils.models import BaseModel, models
from utils import constants

from sales.models import Quote
from product.models import (
    Premium, FeatureCustomerSegmentScore, Feature
)
import math


class Contact(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    phone_no = models.CharField(max_length=10)
    email = models.EmailField(max_length=64, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    occupation = models.IntegerField(
        choices=constants.OCCUPATION_CHOICES,
        default=constants.OCCUPATION_DEFAULT_CHOICE)
    is_married = models.BooleanField(default=False)
    is_parent_dependent = models.BooleanField(default=False)
    other_dependents = models.IntegerField(default=0)
    income = models.FloatField(default=0.0)
    no_of_kids = models.IntegerField(default=0)
    status = models.IntegerField(
        choices=((0, 'Fresh'), (1, 'Other')), default=0)
    medical_history = models.BooleanField(default=False)
    is_default = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('user', 'phone_no',)


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
    status = models.IntegerField(
        choices=constants.LEAD_STATUS_CHOICES, default=0)
    stage = models.IntegerField(
        choices=constants.LEAD_STAGE_CHOICES, default=0)
    # notes = models.ManyToManyField(Note)
    final_score = models.FloatField(default=0.0, db_index=True)
    effective_age = models.IntegerField(default=0)
    tax_saving = models.FloatField(default=0.30)
    wellness_rewards = models.FloatField(default=0.10)
    health_checkups = models.FloatField(default=0.0)
    pincode = models.CharField(max_length=6, null=True)
    adults = models.IntegerField(default=0)
    childrens = models.IntegerField(default=0)
    family = JSONField(default=dict)
    __original_final_score = None

    def save(self, *args, **kwargs):
        try:
            self.__class__.objects.get(pk=self.id)
            if self.final_score != self.__original_final_score:
                self.refresh_quote_data()
        except Lead.DoesNotExist:
            self.parse_family_json()
        super(Lead, self).save(*args, **kwargs)
        self.__original_final_score = self.final_score

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
        return [
            query for query in queryset if self.effective_age in range(
                query.min_age, query.max_age + 1)]

    def refresh_quote_data(self):
        quotes = self.get_quotes()
        if quotes.exists():
            quotes.delete()
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

    def get_recommendated_quotes(self):
        return self.quote_set.all().order_by('-recommendation_score')[:5]

    def get_quotes(self):
        return self.quote_set.all().order_by('-recommendation_score')

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
            self.contact.name if self.contact else 'Contact',
            self.category.name)
