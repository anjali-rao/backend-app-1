# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.model import BaseModel, models
from utils import (
    constants, get_choices, get_upload_path, genrate_random_string
)

from django.contrib.postgres.fields import JSONField, ArrayField
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.dispatch import receiver
from django.core.cache import cache

from goplannr.settings import JWT_SECRET

import uuid

import jwt


class Account(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_no = models.CharField(max_length=10, unique=True)
    alternate_no = models.CharField(max_length=10, null=True, blank=True)
    pan_no = models.CharField(max_length=10, null=True, blank=True)
    aadhar_no = models.CharField(max_length=12, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(
        choices=get_choices(constants.GENDER), max_length=8,
        null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)


class Campaign(BaseModel):
    description = models.CharField(max_length=32)


class User(AbstractUser):
    account = models.ForeignKey(Account, null=True, blank=True)
    user_type = models.CharField(
        choices=get_choices(constants.USER_TYPE), max_length=16,
        default=constants.DEFAULT_USER_TYPE)
    campaign = models.ForeignKey(Campaign, null=True, blank=True)
    hexa_code = models.CharField(max_length=8)
    logo = models.FileField()
    categories = JSONField(default=constants.USER_CATEGORIES)
    active = models.BooleanField(default=False)
    flag = JSONField(default=constants.USER_FLAG)
    company = models.CharField(max_length=64, null=True, blank=True)
    referral_code = models.CharField(max_length=8, null=True, blank=True)
    referral_reference = models.CharField(max_length=8, null=True, blank=True)

    def __unicode__(self):
        return self.username

    @classmethod
    def get_authenticated_user(cls, token):
        try:
            payload = jwt.decode(token, JWT_SECRET)
            return cls.objects.get(account__id=payload.get('user_id'))
        except cls.DoesNotExist:
            return None
        except jwt.InvalidTokenError:
            return None

    def generate_referral_code(self):
        import random
        code = self.first_name.replace(' ','').lower()[:3] + self.account.phone_no[-3:] # noqa
        if User.objects.filter(referral_code=code).exists():
            while User.objects.filter(referral_code=code).exists():
                code = '%s%s' % (
                    self.first_name.lower()[:3], random.randint(111, 999))
        self.referral_code = code

    def get_authorization_key(self):
        return jwt.encode(
            {'user_id': str(self.account.id)},
            JWT_SECRET, algorithm='HS256')

    def get_accounts(self):
        return self.bankaccount_set.filter(is_active=True)

    def send_notification(self, **kwargs):
        return getattr(self, 'send_%s' % kwargs['type'])(kwargs)

    def send_sms(self, kwargs):
        from users.tasks import send_sms
        send_sms(self.account.phone_no, kwargs['message'])

    @classmethod
    def generate_username(cls):
        username = genrate_random_string(7)
        if User.objects.filter(username=username).exists():
            while User.objects.filter(username=username).exists():
                username = genrate_random_string(7)
        return username

    @classmethod
    def validate_referral_code(cls, code):
        return cls.objects.filter(referral_code=code) or not code

    @property
    def account_no(self):
        return self.bankaccount_set.get(default=True).account_no

    @property
    def ifsc(self):
        return self.bankaccount_set.get(default=True).branch.ifsc

    @property
    def bank_name(self):
        return self.bankaccount_set.get(default=True).branch.bank.name

    @classmethod
    def send_otp(cls, phone_no):
        from users.tasks import send_sms
        return send_sms(
            phone_no,
            constants.OTP_MESSAGE % cls.generate_otp(phone_no))

    @staticmethod
    def generate_otp(phone_no):
        import random
        otp = cache.get(phone_no)
        if not otp:
            otp = random.randint(1000, 9999)
            cache.set(phone_no, otp, constants.OTP_TTL)
        return otp

    @staticmethod
    def verify_otp(phone_no, otp):
        return otp == cache.get(phone_no)


class UserDetails(BaseModel):
    user = models.OneToOneField(User)
    agent_code = models.CharField(max_length=16)
    branch_code = models.CharField(max_length=16)
    designation = models.CharField(max_length=16)
    channel = models.CharField(max_length=16)
    status = models.CharField(max_length=32)
    languages = ArrayField(
        models.CharField(max_length=16), default=[], blank=True, null=True)
    certifications = ArrayField(
        models.CharField(max_length=16), default=[], blank=True, null=True)
    qualifications = ArrayField(
        models.CharField(max_length=16), default=[], blank=True, null=True)
    short_description = models.TextField()
    long_description = models.TextField()


class Documents(BaseModel):
    user = models.ForeignKey(User)
    doc_type = models.CharField(
        choices=get_choices(constants.DOC_TYPES), max_length=16)
    file = models.FileField(upload_to=get_upload_path)

    def __unicode__(self):
        return self.doc_type


class Bank(models.Model):
    name = models.CharField(max_length=256)
    is_active = models.BooleanField(default=False)

    def __unicode__(self):
        return self.bank_name


class BankBranch(models.Model):
    bank = models.ForeignKey(Bank)
    branch_name = models.CharField(max_length=128)
    ifsc = models.CharField(max_length=15, unique=True)
    micr = models.CharField(max_length=128)
    city = models.CharField(max_length=64)

    def __unicode__(self):
        return '%s => %s:%s' % (self.bank_name, self.branch_name, self.ifsc)


class BankAccount(BaseModel):
    user = models.ForeignKey(User)
    branch = models.OneToOneField(BankBranch)
    account_no = models.IntegerField()
    default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        try:
            if self.default and BankAccount.objects.filter(
                    default=True).exists():
                self.default = False
        except BankAccount.DoesNotExist:
            self.default = True
        super(BankAccount, self).save(*args, **kwargs)


@receiver(post_save, sender=User, dispatch_uid="action%s" % str(now()))
def user_post_save(sender, instance, created, **kwargs):
    if created:
        if instance.account:
            message = {
                'message': constants.USER_CREATION_MESSAGE,
                'type': 'sms'
            }
            instance.send_notification(**message)


@receiver(post_save, sender=Account, dispatch_uid="action%s" % str(now()))
def account_post_save(sender, instance, created, **kwargs):
    if created:
        message = {
            'message': constants.USER_CREATION_MESSAGE,
            'type': 'sms'
        }
        instance.send_notification(**message)
