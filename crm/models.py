# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import constants as Constants, get_choices, get_kyc_upload_path

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.dispatch import receiver
from django.core.cache import cache


class Lead(BaseModel):
    user = models.ForeignKey('users.user', on_delete=models.CASCADE)
    contact = models.ForeignKey(
        'crm.Contact', null=True, blank=True, on_delete=models.CASCADE)
    campaign = models.ForeignKey(
        'users.Campaign', null=True, blank=True, on_delete=models.CASCADE)
    pincode = models.CharField(max_length=6, null=True)
    bookmark = models.BooleanField(default=False)
    ignore = models.BooleanField(default=False)

    class Meta:
        ordering = ('-bookmark',)

    def create_opportunity(self, validated_data):
        instance = Opportunity.objects.create(
            lead_id=self.id, category_id=validated_data['category_id'])
        instance.update_category_opportunity(validated_data)
        return instance

    def get_quotes(self):
        from sales.models import Quote
        return Quote.objects.filter(
            opportunity__lead_id=self.id,
            ignore=False).exclude(status='rejected')

    def __str__(self):
        return "%s - Contact: %s" % (
            self.user.get_full_name(),
            self.contact.first_name if self.contact else 'Pending')


class Opportunity(BaseModel):
    lead = models.ForeignKey('crm.Lead', on_delete=models.CASCADE)
    category = models.ForeignKey('product.Category', on_delete=models.CASCADE)
    details = None

    def __str__(self):
        return '%s: %s' % (self.category.name, self.lead.__str__())

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        if self.category:
            self.category_name = self.category.name.replace(' ', '').lower()
            if hasattr(self, self.category_name):
                self.category_opportunity = getattr(self, self.category_name)

    def save(self, *args, **kw):
        cache.delete('USER_CONTACTS:%s' % self.lead.user_id)
        super(self.__class__, self).save(*args, **kw)

    def create_category_opportunity(self):
        ContentType.objects.get(
            model=self.category_name, app_label='crm'
        ).model_class().objects.create(opportunity_id=self.id)

    def calculate_suminsured(self):
        self.category_opportunity.calculate_suminsured()

    def get_premiums(self, **kw):
        return self.category_opportunity.get_premiums()

    def refresh_quote_data(self, **kw):
        return self.category_opportunity.refresh_quote_data(**kw)

    def get_quotes(self):
        return self.quote_set.filter(ignore=False).order_by(
            '%s__base_premium' % self.category_name)

    def get_recommendated_quotes(self):
        return self.get_quotes()[:5]

    def update_fields(self, **kw):
        for field in kw.keys():
            setattr(self, field, kw[field])
        self.save()

    def update_category_opportunity(self, validated_data):
        self.refresh_from_db()
        category_opportunity = getattr(self, self.category_name)
        fields = dict.fromkeys(Constants.CATEGORY_OPPORTUNITY_FIELDS_MAPPER[
            self.category_name], None)
        for field in fields.keys():
            fields[field] = validated_data.get(field, getattr(
                category_opportunity, field))
            if isinstance(fields[field], str):
                fields[field] = fields[field].lower()
        category_opportunity.update_fields(**fields)
        return category_opportunity

    @property
    def city(self):
        from users.models import Pincode
        pincodes = Pincode.objects.filter(pincode=self.lead.pincode)
        if pincodes.exists():
            return pincodes.get().city

    @property
    def citytier(self):
        if self.lead.pincode in Constants.NCR_PINCODES or self.city in Constants.MUMBAI_AREA_TIER: # noqa
            return Constants.MUMBAI_NCR_TIER
        return Constants.ALL_INDIA_TIER

    @property
    def companies_id(self):
        return self.lead.user.get_companies().values_list('id', flat=True)


class Contact(BaseModel):
    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, null=True, blank=True)
    address = models.ForeignKey(
        'users.Address', null=True, blank=True, on_delete=models.CASCADE)
    gender = models.CharField(
        max_length=16, choices=get_choices(Constants.GENDER),
        null=True, blank=True)
    phone_no = models.CharField(max_length=20, null=True, blank=True)
    first_name = models.CharField(max_length=32, blank=True)
    middle_name = models.CharField(max_length=32, blank=True)
    last_name = models.CharField(max_length=32, blank=True)
    email = models.EmailField(max_length=64, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    occupation = models.CharField(
        choices=get_choices(Constants.OCCUPATION_CHOICES), null=True,
        default=Constants.OCCUPATION_DEFAULT_CHOICE, blank=True, max_length=32)
    marital_status = models.CharField(
        choices=get_choices(
            Constants.MARITAL_STATUS), max_length=32, null=True, blank=True)
    annual_income = models.CharField(max_length=48, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.first_name = self.first_name.lower()
        self.last_name = self.last_name.lower()
        super(self.__class__, self).save(*args, **kwargs)

    def __str__(self):
        full_name = self.get_full_name()
        return '%s - %s' % ((
            full_name if full_name else 'Parent'
        ), self.phone_no)

    def update_fields(self, **kw):
        for field in kw.keys():
            setattr(self, field, kw[field])
        self.save()

    def is_kyc_required(self):
        kyc_docs = self.kycdocument_set.all()
        if kyc_docs.exists():
            return kyc_docs.latest('modified').file is not None
        return False

    def get_full_name(self):
        full_name = '%s %s %s' % (
            self.first_name, self.middle_name, self.last_name)
        return full_name.strip().title()


class KYCDocument(BaseModel):
    contact = models.ForeignKey(
        'crm.Contact', on_delete=models.CASCADE, null=True, blank=True)
    document_number = models.CharField(max_length=64)
    document_type = models.CharField(
        choices=get_choices(Constants.KYC_DOC_TYPES), max_length=16)
    file = models.FileField(
        upload_to=get_kyc_upload_path, null=True, blank=True)


@receiver(post_save, sender=Opportunity, dispatch_uid="action%s" % str(now()))
def opportunity_post_save(sender, instance, created, **kwargs):
    if created:
        instance.create_category_opportunity()
