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


class Account(AbstractUser):
    phone_no = models.CharField(max_length=10)
    alternate_no = models.CharField(max_length=10, null=True, blank=True)
    pan_no = models.CharField(max_length=10, null=True, blank=True)
    aadhar_no = models.CharField(max_length=12, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(
        choices=get_choices(constants.GENDER), max_length=8,
        null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)

    def send_notification(self, **kwargs):
        return getattr(self, 'send_%s' % kwargs['type'])(kwargs)

    def send_sms(self, kwargs):
        from users.tasks import send_sms
        send_sms(self.phone_no, kwargs['message'])

    def get_default_user(self):
        users = self.user_set.filter(is_active=True)
        if not users.exists():
            return False
        if users.filter(user_type='enterprise').exists():
            return users.earliest('created')
        if users.filter(user_type='pos').exists():
            return users.earliest('created')
        return users.earliest('created')

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

    @classmethod
    def get_account(cls, phone_no):
        accounts = cls.objects.filter(phone_no=phone_no)
        if accounts.exists():
            return accounts.get()
        acc = cls.objects.create(username=cls.generate_username())
        acc.phone_no = phone_no
        acc.save()
        return acc

    @classmethod
    def generate_username(cls):
        username = genrate_random_string(10)
        if cls.objects.filter(username=username).exists():
            while cls.objects.filter(username=username).exists():
                username = genrate_random_string(10)
        return username


class User(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account)
    user_type = models.CharField(
        choices=get_choices(constants.USER_TYPE), max_length=16,
        default=constants.DEFAULT_USER_TYPE)
    campaign = models.ForeignKey('users.Campaign', null=True, blank=True)
    enterprise = models.ForeignKey('users.Enterprise')
    flag = JSONField(default=constants.USER_FLAG)
    is_active = models.BooleanField(default=False)

    def __unicode__(self):
        return self.account.username

    def get_authorization_key(self):
        # TO DOs:  Change to basic auth
        return jwt.encode(
            {'user_id': str(self.id)},
            JWT_SECRET, algorithm='HS256')

    @classmethod
    def get_authenticated_user(cls, token):
        try:
            payload = jwt.decode(token, JWT_SECRET)
            return cls.objects.get(account__id=payload.get('user_id'))
        except cls.DoesNotExist:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_accounts(self):
        return self.bankaccount_set.filter(is_active=True)

    @staticmethod
    def validate_referral_code(code):
        return Referral.objects.filter(referral_code=code).exists()

    @staticmethod
    def get_referral_details(code):
        referrals = Referral.objects.filter(referral_code=code)
        if not referrals.exists():
            return {
                'user_type': constants.DEFAULT_USER_TYPE,
                'enterprise_id': Enterprise.objects.get(
                    name=constants.DEFAULT_ENTERPRISE).id
            }
        referral = referrals.get()
        return {
            'enterprise_id': referral.enterprise or Enterprise.objects.get(
                name=constants.DEFAULT_ENTERPRISE).id,
            'user_type': 'enterprise' if referral.enterprise else constants.DEFAULT_USER_TYPE # noqa
        }

    def generate_referral(self, referral_reference=None):
        import random
        code = '%s%s' % (
            self.account.first_name.lower()[:3], self.account.phone_no[-3:])
        if Referral.objects.filter(referral_code=code).exists():
            while Referral.objects.filter(referral_code=code).exists():
                code = '%s%s' % (
                    self.account.first_name.lower()[:3],
                    random.randint(111, 999))
        return Referral.objects.create(
            referral_code=code, referral_reference=referral_reference)

    @property
    def account_no(self):
        return self.bankaccount_set.get(default=True).account_no

    @property
    def ifsc(self):
        return self.bankaccount_set.get(default=True).branch.ifsc

    @property
    def bank_name(self):
        return self.bankaccount_set.get(default=True).branch.bank.name


class Campaign(BaseModel):
    description = models.CharField(max_length=32)
    start_date = models.DateField(null=True, blank=True)


class Enterprise(BaseModel):
    name = models.CharField(max_length=64)
    hexa_code = models.CharField(max_length=8, default='#005db1')
    logo = models.ImageField(upload_to=constants.ENTERPRISE_UPLOAD_PATH)

    def __unicode__(self):
        return self.name

    @property
    def companies(self):
        return self.company_set.all()

    def generate_referral_code(self):
        pass


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


class Referral(BaseModel):
    referral_code = models.CharField(max_length=10, unique=True)
    referral_reference = models.CharField(max_length=10, null=True, blank=True)
    enterprise = models.ForeignKey(Enterprise, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True)


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


class State(models.Model):
    name = models.CharField(max_length=128)

    def __unicode__(self):
        return self.name


class Pincode(models.Model):
    pincode = models.CharField(max_length=6, unique=True)
    city = models.CharField(max_length=64)
    state = models.ForeignKey(State)
    city_type = models.IntegerField(
        choices=constants.CITY_TIER, default=2)

    def __unicode__(self):
        return '%s - %s - (%s)' % (self.pincode, self.city, self.state.name)


@receiver(post_save, sender=User, dispatch_uid="action%s" % str(now()))
def user_post_save(sender, instance, created, **kwargs):
    if created:
        if not instance.__class__.objects.filter(
                user_type=constants.DEFAULT_USER_TYPE).exists():
            new_user = instance.__class__.objects.create(
                account_id=instance.account.id,
                user_type=constants.DEFAULT_USER_TYPE,
                enterprise_id=Enterprise.objects.get(
                    name=constants.DEFAULT_ENTERPRISE).id,
                is_active=True
            )
            new_user.generate_referral()


@receiver(post_save, sender=Account, dispatch_uid="action%s" % str(now()))
def account_post_save(sender, instance, created, **kwargs):
    message = {
        'message': constants.USER_CREATION_MESSAGE % (
            instance.phone_no),
        'type': 'sms'
    }
    instance.send_notification(**message)
