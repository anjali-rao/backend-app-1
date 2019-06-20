# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import constants as Constants, get_choices
from django.core.cache import cache


class Earning(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.PROTECT)
    amount = models.FloatField(default=0.0)
    earning_type = models.CharField(
        choices=get_choices(Constants.EARNING_TYPES), max_length=16)
    comment = models.TextField(blank=True, null=True)
    status = models.CharField(
        choices=get_choices(Constants.EARNING_STATUS), max_length=16)
    transaction_allowed = models.BooleanField(default=False)
    text = models.CharField(max_length=512)
    payable_date = models.DateTimeField()
    ignore = models.BooleanField(default=False)

    def __str__(self):
        return self.user.__str__()

    def save(self, *args, **kwargs):
        if not self.__class__.objects.filter(
                pk=self.id).exists() and self.earning_type == 'referral':
            self.text = (getattr(
                Constants, ('%s_TEXT' % self.earning_type).upper()
            ) % self.get_text_paramaters())
        cache.delete('USER_EARNINGS:%s' % self.user_id)
        super(self.__class__, self).save(*args, **kwargs)

    def get_text_paramaters(self):
        if self.earning_type == 'referral':
            from users.models import Referral
            return Referral.objects.get(
                referral_reference=self.user.referral.referral_code
            ).user.account.get_full_name()

    @classmethod
    def get_user_earnings(cls, user_id, earning_type=None):
        query = dict(user_id=user_id)
        if earning_type:
            query['earning_type'] = earning_type
        return cls.objects.filter(**query).aggregate(
            s=models.Sum('amount'))['s'] or 0


class Commission(BaseModel):
    earning = models.OneToOneField(
        'earnings.Earning', on_delete=models.PROTECT, null=True, blank=True)
    application = models.ForeignKey(
        'sales.Application', on_delete=models.CASCADE)
    amount = models.FloatField(default=0.0)
    updated = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.updated and not self.__class__.objects.get(pk=self.id).updated:
            # To do replace with policy
            earning_text = Constants.COMMISSION_TEXT % (
                '10884022', '17/05/2019',
                self.application.client.get_full_name())
            self.earning = Earning.objects.create(
                user_id=self.application.quote.lead.user_id,
                amount=self.amount, earning_type='commission',
                status='pending', text=earning_text,
                payable_date='2019-06-02')
        super(self.__class__, self).save(*args, **kwargs)


class Incentive(BaseModel):
    earning = models.OneToOneField(
        'earnings.Earning', on_delete=models.PROTECT, null=True, blank=True)
    user = models.ForeignKey('users.User', on_delete=models.PROTECT)
    application = models.ForeignKey(
        'sales.Application', on_delete=models.CASCADE, null=True, blank=True)
    amount = models.FloatField(default=0.0)
    comment = models.TextField(null=True, blank=True)
    criteria = models.CharField(max_length=128, null=True, blank=True)
    updated = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.updated and not self.__class__.objects.get(pk=self.id).updated:
            earning_text = Constants.INCENTIVE_TEXT % (
                'Creating lead more than 4')
            self.earning = Earning.objects.create(
                user_id=self.user_id, amount=self.amount,
                earning_type='incentive', status='pending',
                text=earning_text, comment=self.comment,
                payable_date='2019-06-02')
        super(self.__class__, self).save(*args, **kwargs)
