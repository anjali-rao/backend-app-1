# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.postgres.fields import JSONField

from utils.model import BaseModel, models
from utils import constants

from sales.models import Quote, QuoteFeature


class Contact(BaseModel):
    user = models.ForeignKey('users.User')
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

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('user', 'phone_no',)


class Lead(BaseModel):
    user = models.ForeignKey('users.user')
    contact = models.ForeignKey('crm.Contact', null=True, blank=True)
    category = models.ForeignKey('product.Category')
    amount = models.FloatField(default=0.0)
    final_score = models.FloatField(default=0.0)
    status = models.IntegerField(
        choices=constants.LEAD_STATUS_CHOICES, default=0)
    stage = models.IntegerField(
        choices=constants.LEAD_STAGE_CHOICES, default=0)
    product_id = models.IntegerField(null=True, blank=True)
    # notes = models.ManyToManyField(Note)
    campaign = models.ForeignKey('users.Campaign', null=True, blank=True)
    max_age = models.IntegerField(default=0)
    min_age = models.IntegerField(default=0)
    customer_segment = models.ForeignKey(
        'product.CustomerSegment', null=True, blank=True)
    adult = models.IntegerField(default=0)
    pincode = models.CharField(max_length=6)
    children = models.IntegerField(default=0)
    family = JSONField(default={})
    tax_saving = models.FloatField(default=0.30)
    wellness_rewards = models.FloatField(default=0.10)
    health_checkups = models.FloatField(default=0.0)
    __original_final_score = None

    def save(self, *args, **kwargs):
        try:
            self.__class__.objects.get(pk=self.id)
            if self.final_score != self.__original_final_score:
                self.refresh_quote_data()
        except Lead.DoesNotExist:
            self.parse_family()
            self.customer_segment_id = self.get_customer_segment().id
        super(Lead, self).save(*args, **kwargs)
        self.__original_final_score = self.final_score

    def parse_family(self):
        ages = self.family.values()
        self.min_age = min(ages)
        self.max_age = max(ages)
        self.adult = len([i for i in ages if i > constants.ADULT_AGE_LIMIT])
        self.children = len(ages) - self.adult

    def calculate_final_score(self):
        from questionnaire.models import Response
        self.final_score = Response.objects.select_related('answer').filter(
            lead_id=self.id).aggregate(
                s=models.Sum('answer__score'))['s'] * 100000
        self.save()

    def refresh_quote_data(self):
        from product.models import Premium, FeatureCustomerSegmentScore
        quotes = self.get_quotes()
        if quotes.exists():
            quotes.delete()
        premiums = Premium.objects.select_related('product_variant').filter(
            product_variant__company_category__category_id=self.category_id,
            min_age__lte=self.min_age, max_age__gte=self.max_age,
            sum_insured=self.final_score, product_variant__adult=self.adult,
            product_variant__city=self.city,
            product_variant__children=self.children)
        for premium in premiums:
            quote = Quote.objects.create(
                lead_id=self.id, premium_id=premium.id)
            features = premium.product_variant.feature_set.all()
            for feature in features:
                feature_score = FeatureCustomerSegmentScore.objects.filter(
                    feature_id=feature.id,
                    customer_segment_id=self.customer_segment.id).last()
                QuoteFeature.objects.create(
                    quote_id=quote.id, feature_id=feature.id,
                    score=feature_score.score
                )

    def get_customer_segment(self):
        from product.models import CustomerSegment
        segment_name = 'young adult'
        if 'self' in self.family:
            age = self.family['self']
            if age < 35:
                segment_name = 'young adult'
            if any(x in self.family for x in ['mother', 'father']) and age < 35: # noqa
                segment_name = 'young adult with dependent parents'
            if 'spouse' in self.family:
                if age < 35:
                    segment_name = 'young couple'
                if age > 50:
                    segment_name = 'senior citizens'
                if self.family.get('kid') >= 1 and age < 40:
                    segment_name = 'young family'
                if self.family.get('kid') >= 1 and age < 60:
                    segment_name = 'middle aged family'
        return CustomerSegment.objects.get(name=segment_name)

    def get_quotes(self):
        return self.quote_set.all()

    @property
    def city(self):
        """ Return City by looking into db
        """
        return

    def next_activity_date_time(self):
        return "No Activity Found"

    def __str__(self):
        return "%s - %s" % (
            self.contact.name if self.contact else 'Contact',
            self.category.name)
