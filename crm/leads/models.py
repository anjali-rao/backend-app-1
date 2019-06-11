# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db import models

from questionnaire.models import Response
from product.models import (
    HealthPremium, FeatureCustomerSegmentScore, Feature)
from sales.models import Quote
import math


class HealthInsurance(models.Model):
    base = models.OneToOneField('crm.Lead', on_delete=models.PROTECT)
    customer_segment = models.ForeignKey(
        'product.CustomerSegment', null=True, blank=True,
        on_delete=models.CASCADE)
    predicted_suminsured = models.FloatField(default=0.0, db_index=True)
    effective_age = models.IntegerField(default=0)
    adults = models.IntegerField(default=0)
    gender = models.CharField(max_length=12, null=True)
    childrens = models.IntegerField(default=0)
    family = JSONField(default=dict)
    tax_saving = models.FloatField(default=0.30)
    wellness_reward = models.FloatField(default=0.10)
    health_checkup = models.FloatField(default=0.0)

    def __str__(self):
        return 'HealthInsurance - Lead'

    def save(self, *args, **kwargs):
        try:
            current = self.__class__.objects.get(pk=self.id)
            if self.predicted_suminsured != current.predicted_suminsured:
                self.refresh_quote_data()
                self.stage = 'inprogress'
            if self.family != current.family:
                self.parse_family_details()
        except self.__class__.DoesNotExist:
            if self.family:
                self.parse_family_details()
        super(self.__class__, self).save(*args, **kwargs)

    def parse_family_details(self):
        ages = list(map(int, self.family.values()))
        if 'daughter_total' in self.family:
            self.childrens += self.family['daughter_total']
            ages.remove(int(self.family['daughter_total']))
        if 'son_total' in self.family:
            self.childrens += self.family['son_total']
            ages.remove(int(self.family['son_total']))
        self.effective_age = int(max(ages))
        self.adults = len(ages)
        self.customer_segment_id = self.get_customer_segment().id

    def calculate_suminsured(self):
        score = math.ceil(
            Response.objects.select_related('answer').filter(
                lead_id=self.base_id).aggregate(
                s=models.Sum('answer__score'))['s'])
        if score <= 3:
            score = 3
        elif score <= 5:
            score = 5
        elif score <= 7:
            score = 7
        elif score <= 10:
            score = 10
        elif score <= 20:
            score = 20
        else:
            score = 50
        self.predicted_suminsured = score * 100000
        self.save()

    def get_customer_segment(self, **kw):
        from product.models import CustomerSegment
        responses = Response.objects.select_related(
            'answer', 'question').filter(lead_id=self.id)
        segment_name = 'young_adult'
        effective_age = kw.get('effective_age', self.effective_age)
        childrens = kw.get('childrens', self.childrens)
        if 'self_age' in kw:
            age = int(kw['self_age'])
            if age <= 35:
                segment_name = 'young_adult'
            if any(x in kw for x in ['mother_age', 'father_age']) and age < 35:
                segment_name = 'young_adult_with_dependent_parents'
            if age > 50:
                segment_name = 'senior_citizens'
            if 'spouse_age' in kw:
                if age < 35:
                    segment_name = 'young_couple'
                if age > 50:
                    segment_name = 'senior_citizens'
                if childrens >= 1 and age < 40:
                    segment_name = 'young_family'
                if childrens >= 1 and age < 60:
                    segment_name = 'middle_aged_family'
            emp_resp = responses.filter(question__title='Occupation')
            if emp_resp.exists() and emp_resp.filter(
                    answer__answer='Self Employed or Business').exists():
                segment_name = 'self_employed'
        if effective_age < 40 and effective_age >= 1:
            segment_name = 'young_family'
        elif effective_age <= 35 and kw.get('adults', self.adults) == 1:
            segment_name = 'young_adult'
        elif effective_age <= 35 and kw.get('adults', self.adults) == 2:
            segment_name = 'young_couple'
        elif effective_age < 60 and childrens >= 1:
            segment_name = 'middle_aged_family'
        elif effective_age >= 50:
            segment_name = 'senior_citizens'
        return CustomerSegment.objects.only('id').get(name=segment_name)

    def get_premiums(self, **kw):
        query = dict()
        queryset = HealthPremium.objects.select_related(
            'product_variant').filter(
            suminsured_range__contains=int(kw.get(
                'score', self.predicted_suminsured)),
            adults=kw.get('adults', self.adults), ignore=False,
            citytier__in=kw.get('citytier', self.base.citytier),
        )
        if 'product_variant_id' in kw:
            query['product_variant_id'] = kw['product_variant_id']
        if 'category_id' in kw:
            query['product_variant__company_category__category_id'] = kw['category_id'] # noqa
        if kw.get('childrens', self.childrens) <= 4:
            query['childrens'] = kw.get('childrens', self.childrens)
        query.update(dict(
            age_range__contains=kw.get('effective_age', self.effective_age),
            product_variant__company_category__company_id__in=self.base.companies_id # noqa
        ))
        premiums = queryset.filter(**query)
        if not premiums.exists():
            query.pop('product_variant__company_category__company_id__in')
            premiums = queryset.filter(**query)
        return premiums or queryset[:5]

    def refresh_quote_data(self, **kw):
        quotes = self.base.get_quotes()
        if quotes.exists():
            quotes.update(ignore=True)
        content_id = ContentType.objects.get(
            app_label='product', model='healthpremium').id
        for premium in self.get_premiums(**kw):
            feature_masters = premium.product_variant.feature_set.values_list(
                'feature_master_id', flat=True)
            quote = Quote.objects.create(
                lead_id=self.base.id, premium_id=premium.id,
                content_type_id=content_id)
            changed_made = False
            for feature_master_id in feature_masters:
                feature_score = FeatureCustomerSegmentScore.objects.only(
                    'score', 'feature_master_id').filter(
                        feature_master_id=feature_master_id,
                        customer_segment_id=kw.get(
                            'customer_segment_id', self.customer_segment_id)
                ).last()
                if feature_score is not None:
                    if not changed_made:
                        changed_made = False
                    quote.recommendation_score += float(Feature.objects.filter(
                        feature_master_id=feature_master_id).aggregate(
                            s=models.Sum('rating'))['s'] * feature_score.score)
            if changed_made:
                quote.save()

    def update_fields(self, **kw):
        for field in kw.keys():
            setattr(self, field, kw[field])
        self.save()
