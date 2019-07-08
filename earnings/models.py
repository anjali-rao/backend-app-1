# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import constants as Constants, get_choices
from earnings import REASONS

from django.core.cache import cache
from django.utils.timezone import now


class Earning(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.PROTECT)
    amount = models.FloatField(default=0.0)
    earning_type = models.CharField(
        choices=get_choices(Constants.EARNING_TYPES), max_length=16)
    comment = models.TextField(blank=True, null=True)
    status = models.CharField(
        choices=get_choices(Constants.EARNING_STATUS), max_length=32,
        default='collecting_application')
    reason = models.CharField(
        choices=tuple([(x, x) for x in REASONS]), max_length=512,
        null=True, blank=True)
    transaction_allowed = models.BooleanField(default=False)
    text = models.CharField(max_length=512)
    payable_date = models.DateTimeField()
    ignore = models.BooleanField(default=False)

    def __str__(self):
        return self.user.__str__()

    def save(self, *args, **kwargs):
        try:
            current = self.__class__.objects.get(pk=self.id)
            if current.status != self.status:
                self.handle_status_change(current)
        except self.__class__.DoesNotExist:
            pass
        cache.delete('USER_EARNINGS:%s' % self.user_id)
        super(self.__class__, self).save(*args, **kwargs)

    def handle_status_change(self, current):
        app = self.commission.application
        if self.status == 'policy_rejected':
            client = app.client
            if app.__class__.objects.filter(
                    app_client_id=client.id).count() == 1:
                client.is_client = False
                client.save()
                app.client = None
            app.status = 'pending'
            app.stage = 'payment_failed'
            app.save()
        message = self.get_earning_message(app)
        if message:
            self.user.account.send_sms(message)

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

    def get_earning_message(self, app=None):
        return dict(
            application_submitted='Application # %s has been submitted to insurer.' % (app.reference_no),
            policy_rejected='Policy Rejected for application # %s,\nReason %s' % (
                app.reference_no, self.reason),
            policy_followup='Insurer has asked for more information for application # %s,\n Reason %s' % (
                app.reference_no, self.reason),
        ).get(self.status)


class Commission(BaseModel):
    earning = models.OneToOneField(
        'earnings.Earning', on_delete=models.PROTECT, null=True, blank=True)
    application = models.OneToOneField(
        'sales.Application', on_delete=models.CASCADE)
    amount = models.FloatField(default=0.0)
    updated = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.updated and not self.__class__.objects.get(pk=self.id).updated:
            earning_text = Constants.COMMISSION_TEXT % (
                self.application.reference_no, now().date(),
                self.application.proposer.get_full_name())
            from dateutil.relativedelta import relativedelta
            self.earning = Earning.objects.create(
                user_id=self.application.quote.opportunity.lead.user_id,
                amount=self.amount, earning_type='commission',
                text=earning_text, payable_date=now() + relativedelta(days=30))
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
                payable_date=now())
        super(self.__class__, self).save(*args, **kwargs)
