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

from goplannr.settings import JWT_SECRET, BASE_HOST, DEBUG

import uuid

import jwt
from django.utils.translation import ugettext_lazy as _

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType


class Account(AbstractUser):
    phone_no = models.CharField(max_length=10)
    alternate_no = models.CharField(max_length=10, null=True, blank=True)
    pan_no = models.CharField(max_length=10, null=True, blank=True)
    aadhar_no = models.CharField(max_length=12, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(
        choices=get_choices(constants.GENDER), max_length=8,
        null=True, blank=True)
    address = models.ForeignKey(
        'users.Address', null=True, blank=True, on_delete=models.CASCADE)
    pincode = models.ForeignKey(
        'users.Pincode', null=True, blank=True, on_delete=models.CASCADE)

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
        otp = cache.get('OTP:%s' % phone_no)
        if not otp:
            otp = random.randint(1000, 9999)
            cache.set('OTP:%s' % phone_no, otp, constants.OTP_TTL)
        return otp

    @staticmethod
    def verify_otp(phone_no, otp):
        return otp == cache.get('OTP:%s' % phone_no)

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

    @property
    def age(self):
        days = (now().date() - self.dob).days
        return '%s years and %s months' % ((days % 365) / 30, days / 365)

    class Meta:
        verbose_name = _('Account')


class User(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey('users.Account', on_delete=models.CASCADE)
    user_type = models.CharField(
        choices=get_choices(constants.USER_TYPE), max_length=16,
        default=constants.DEFAULT_USER_TYPE)
    campaign = models.ForeignKey(
        'users.Campaign', null=True, blank=True, on_delete=models.CASCADE)
    flag = JSONField(default=constants.USER_FLAG)
    is_active = models.BooleanField(default=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    enterprise_id = models.PositiveIntegerField()
    enterprise = GenericForeignKey('content_type', 'enterprise_id')

    def save(self, *args, **kwargs):
        if not self.__class__.objects.filter(pk=self.id):
            models_name = 'subcriberenterprise'
            if self.user_type == 'enterprise':
                models_name = 'enterprise'
            self.content_type_id = ContentType.objects.get(
                app_label='users', model=models_name).id
        super(User, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.account.get_full_name()

    @property
    def enterprise(self):
        if self.user_type == 'subscriber':
            modelClass = SubcriberEnterprise
        else:
            modelClass = Enterprise
        enterprises = modelClass.objects.filter(id=self.enterprise_id)
        if enterprises.exists():
            return enterprises.get()

    def get_authorization_key(self):
        return jwt.encode(
            {'user_id': str(self.id)},
            JWT_SECRET, algorithm='HS256')

    @classmethod
    def get_authenticated_user(cls, token):
        try:
            payload = jwt.decode(token, JWT_SECRET)
            return cls.objects.get(id=payload.get('user_id'))
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
                'enterprise_id': SubcriberEnterprise.objects.get(
                    name=constants.DEFAULT_ENTERPRISE).id
            }
        referral = referrals.get()
        return {
            'enterprise_id': referral.enterprise or SubcriberEnterprise.objects.get( # noqa
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

    def get_categories(self):
        categories = list()
        for category in self.enterprise.categories.only(
                'name', 'id', 'hexa_code', 'logo'):
            categories.append({
                'id': category.id, 'hexa_code': category.hexa_code,
                'logo': (BASE_HOST if DEBUG else '') + category.logo.url,
                'name': category.name.split(' ')[0]
            })
        return categories


class Campaign(BaseModel):
    description = models.CharField(max_length=32)
    start_date = models.DateField(null=True, blank=True)


class Enterprise(BaseModel):
    name = models.CharField(max_length=64)
    companies = models.ManyToManyField('product.Company', blank=True)
    categories = models.ManyToManyField('product.Category', blank=True)
    hexa_code = models.CharField(max_length=8, default='#005db1')
    logo = models.ImageField(
        upload_to=constants.ENTERPRISE_UPLOAD_PATH,
        default=constants.DEFAULT_LOGO)
    person = GenericRelation(
        User, related_query_name='enterprise_user',
        object_id_field='enterprise_id')

    def __str__(self):
        return self.name

    def generate_referral_code(self):
        pass


class SubcriberEnterprise(BaseModel):
    name = models.CharField(
        max_length=64, default=constants.DEFAULT_ENTERPRISE)
    companies = models.ManyToManyField('product.Company', blank=True)
    categories = models.ManyToManyField('product.Category', blank=True)
    hexa_code = models.CharField(max_length=8, default='#005db1')
    logo = models.ImageField(
        upload_to=constants.ENTERPRISE_UPLOAD_PATH,
        default=constants.DEFAULT_LOGO)
    person = GenericRelation(
        User, related_query_name='subscriber_enterprise_user',
        object_id_field='enterprise_id')

    def __str__(self):
        return self.name

    def generate_referral_code(self):
        pass


class AccountDetails(BaseModel):
    account = models.OneToOneField('users.Account', on_delete=models.CASCADE)
    agent_code = models.CharField(max_length=16)
    branch_code = models.CharField(max_length=16)
    designation = models.CharField(max_length=16)
    channel = models.CharField(max_length=16)
    status = models.CharField(max_length=32)
    languages = ArrayField(
        models.CharField(max_length=16), default=list, blank=True, null=True)
    certifications = ArrayField(
        models.CharField(max_length=16), default=list, blank=True, null=True)
    qualifications = ArrayField(
        models.CharField(max_length=16), default=list, blank=True, null=True)
    short_description = models.TextField()
    long_description = models.TextField()


class Referral(BaseModel):
    referral_code = models.CharField(max_length=10, unique=True)
    referral_reference = models.CharField(max_length=10, null=True, blank=True)
    enterprise = models.ForeignKey(
        'users.Enterprise', null=True, blank=True, on_delete=models.CASCADE)
    user = models.ForeignKey(
        'users.User', null=True, blank=True, on_delete=models.CASCADE)


class Documents(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
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
    bank = models.ForeignKey('users.Bank', on_delete=models.CASCADE)
    branch_name = models.CharField(max_length=128)
    ifsc = models.CharField(max_length=15, unique=True)
    micr = models.CharField(max_length=128)
    city = models.CharField(max_length=64)

    def __unicode__(self):
        return '%s => %s:%s' % (self.bank_name, self.branch_name, self.ifsc)


class BankAccount(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    branch = models.OneToOneField('BankBranch', on_delete=models.CASCADE)
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
    name = models.CharField(max_length=128, db_index=True)

    def __unicode__(self):
        return self.name


class Pincode(models.Model):
    pincode = models.CharField(
        max_length=6, unique=True, db_index=True)
    city = models.CharField(max_length=64, db_index=True)
    state = models.ForeignKey(
        'users.State', null=True, blank=True, on_delete=models.CASCADE)
    city_type = models.IntegerField(
        choices=constants.CITY_TIER, default=3)

    def __unicode__(self):
        return '%s - %s - (%s)' % (self.pincode, self.city, self.state.name)

    @classmethod
    def get_pincode(cls, pincode):
        pincodes = cls.objects.filter(pincode=pincode)
        if pincodes.exists():
            return pincodes.get()
        return None


class Address(BaseModel):
    street = models.CharField(max_length=128)
    pincode = models.ForeignKey('users.Pincode', on_delete=models.CASCADE)

    @property
    def full_address(self):
        return '%s, %s, %s - %s' % (
            self.street, self.pincode.city, self.state, self.pincode)


@receiver(post_save, sender=User, dispatch_uid="action%s" % str(now()))
def user_post_save(sender, instance, created, **kwargs):
    if created:
        pass
# Currently Not required have to implement once product is lauched via cron
#        if not instance.__class__.objects.filter(
#                user_type=constants.DEFAULT_USER_TYPE).exists():
#            new_user = instance.__class__.objects.create(
#                account_id=instance.account.id,
#                user_type=constants.DEFAULT_USER_TYPE,
#                enterprise_id=Enterprise.objects.get(
#                    name=constants.DEFAULT_ENTERPRISE).id,
#                is_active=True
#            )
#            new_user.generate_referral()


@receiver(post_save, sender=Account, dispatch_uid="action%s" % str(now()))
def account_post_save(sender, instance, created, **kwargs):
    if created:
        message = {
            'message': constants.USER_CREATION_MESSAGE % (
                instance.phone_no), 'type': 'sms'
        }
        instance.send_notification(**message)
