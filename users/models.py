# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import (
    constants as Constants, get_choices, get_kyc_upload_path)

from django.contrib.postgres.fields import JSONField, ArrayField
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.dispatch import receiver
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation
from django.db import IntegrityError

from goplannr.settings import JWT_SECRET, DEBUG, SMS_OTP_HASH

import jwt


class Account(AbstractUser):
    phone_no = models.CharField(max_length=10)
    password = models.CharField(_('password'), max_length=128, null=True)
    alternate_no = models.CharField(max_length=10, null=True, blank=True)
    pan_no = models.CharField(max_length=10, null=True, blank=True)
    aadhar_no = models.CharField(max_length=12, null=True, blank=True)
    fcm_id = models.CharField(max_length=256, null=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(
        choices=get_choices(Constants.GENDER), max_length=8,
        null=True, blank=True)
    address = models.ForeignKey(
        'users.Address', null=True, blank=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        user = self.get_default_user()
        if user:
            cache.delete('USER_DETAIL:%s' % user.id)
        super(self.__class__, self).save(*args, **kwargs)

    def send_notification(self, **kwargs):
        return getattr(self, 'send_%s' % kwargs['type'])(kwargs)

    def send_sms(self, kwargs):
        from users.tasks import send_sms
        send_sms.delay(self.phone_no, kwargs['message'])

    def get_default_user(self):
        users = self.user_set.filter(is_active=True)
        if not users.exists():
            return False
        if users.filter(user_type='enterprise').exists():
            return users.earliest('created')
        if users.filter(user_type='pos').exists():
            return users.earliest('created')
        return users.earliest('created')

    def upload_docs(self, validated_data, fields):
        for field in fields:
            name = validated_data[field].name.split('.')
            file_name = '%s_%s_%s.%s' % (
                self.id, name[0], now().date().isoformat(), name[1])
            doc = KYCDocument.objects.create(
                document_type=field, account_id=self.id)
            doc.file.save(file_name, validated_data[field])
            validated_data[field] = doc.file.url
        return validated_data

    @classmethod
    def send_otp(cls, prefix, phone_no):
        from users.tasks import send_sms
        return send_sms.delay(
            phone_no,
            Constants.OTP_MESSAGE % (
                cls.generate_otp(prefix, phone_no), SMS_OTP_HASH))

    @staticmethod
    def generate_otp(prefix, phone_no):
        import random
        otp = cache.get(prefix)
        if not otp:
            otp = random.randint(1000, 9999)
            cache.set(prefix, otp, Constants.OTP_TTL)
        return otp

    @staticmethod
    def verify_otp(phone_no, otp):
        return otp == cache.get('OTP:%s' % phone_no)

    @classmethod
    def get_account(cls, phone_no, first_name, last_name):
        accounts = cls.objects.filter(phone_no=phone_no)
        if accounts.exists():
            raise IntegrityError(Constants.DUPLICATE_ACCOUNT)
#            return accounts.get()
        acc = cls.objects.create(username=cls.generate_username(
            first_name, last_name))
        acc.phone_no = phone_no
        acc.save()
        return acc

    @classmethod
    def generate_username(cls, first_name, last_name):
        username = ('%s-%s' % (first_name, last_name)).lower()
        accounts = cls.objects.filter(
            first_name__icontains=first_name,
            last_name__icontains=last_name)
        if accounts.exists() and accounts.filter(username=username).exists():
            username += '-' + str(accounts.count())
        return username

    @property
    def age(self):
        days = (now().date() - self.dob).days
        return '%s years and %s months' % ((days % 365) / 30, days / 365)

    @property
    def profile_pic(self):
        docs = KYCDocument.objects.filter(
            document_type='photo', account_id=self.id)
        if docs.exists():
            return docs.last().file
        return KYCDocument.objects.filter(
            document_type='photo', account_id=1).first().file

    def __str__(self):
        return 'Account: %s - %s' % (
            self.username, self.phone_no)

    class Meta:
        verbose_name = _('Account')


class User(BaseModel):
    account = models.ForeignKey('users.Account', on_delete=models.CASCADE)
    user_type = models.CharField(
        choices=get_choices(Constants.USER_TYPE), max_length=16,
        default=Constants.DEFAULT_USER_TYPE)
    campaign = models.ForeignKey(
        'users.Campaign', null=True, blank=True, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    enterprise = models.ForeignKey(
        'users.Enterprise', on_delete=models.PROTECT)
    flag = JSONField(default=Constants.USER_FLAG)
    is_active = models.BooleanField(default=False)
    manager_id = models.CharField(max_length=48, null=True, blank=True)

    def save(self, *args, **kwargs):
        cache.delete('USER_DETAIL:%s' % self.id)
        super(self.__class__, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('user_type', 'account')

    def __str__(self):
        return self.account.get_full_name()

    def get_authorization_key(self):
        return jwt.encode(
            {'user_id': str(self.id)},
            JWT_SECRET, algorithm='HS256')

    def get_full_name(self):
        return self.account.get_full_name()

    @classmethod
    def get_authenticated_user(cls, token):
        try:
            payload = jwt.decode(token, JWT_SECRET)
            return cls.objects.get(id=payload.get('user_id'))
        except Exception:
            pass
        return None

    def get_accounts(self):
        return self.bankaccount_set.filter(is_active=True)

    def generate_referral(self, referral_reference=None):
        import random
        code = ('%s%s' % (
            self.account.first_name.lower()[:3], self.account.phone_no[-5:])
        ).upper()
        if Referral.objects.filter(code=code).exists():
            while Referral.objects.filter(code=code).exists():
                code = ('%s%s' % (
                    self.account.first_name.lower()[:3],
                    random.randint(11111, 99999))).upper()
        return Referral.objects.create(
            code=code, reference_code=referral_reference,
            user_id=self.id)

    def get_categories(self):
        categories = list()
        from product.models import Category
        for category in Category.objects.only(
                'name', 'id', 'hexa_code', 'logo', 'is_active'):
            is_active = False
            categorys = self.enterprise.categories.filter(id=category.id)
            if categorys.exists():
                is_active = categorys.get().is_active
            categories.append(dict(
                id=category.id, hexa_code=category.hexa_code,
                name=category.name.split(' ')[0], is_active=is_active,
                logo=(
                    Constants.DEBUG_HOST if DEBUG else '') + category.logo.url
            ))
        categories = sorted(
            categories, key=lambda category: Constants.CATEGORY_ORDER.get(
                category['name'], 1))
        return categories

    def get_companies(self):
        return self.enterprise.companies.filter(is_active=True)

    def get_applications(self, status=None):
        from sales.models import Application
        query = dict(quote__opportunity__lead__user_id=self.id)
        if status and isinstance(status, list):
            query['status__in'] = status
        elif status:
            query['status'] = status
        return Application.objects.filter(**query)

    def get_policies(self):
        from sales.models import Policy
        return Policy.objects.filter(
            application__quote__opportunity__lead__user_id=self.id)

    def get_earnings(self, earning_type=None):
        from earnings.models import Earning
        return Earning.get_user_earnings(self.id, earning_type)

    def get_rules(self):
        rules = dict.fromkeys(Constants.PROMO_RULES_KEYS, False)
        promo_code = self.enterprise.promocode.code.split('-')[1:]
        for rule_code in promo_code:
            if not rule_code.isdigit():
                rule_code = 1
            rules.update(Constants.PROMO_RULES[int(rule_code)])
        if self.enterprise.enterprise_type != 'subscriber':
            rules['kyc_allowed'] = True
        return rules

    def get_collaterals(self):
        from content.models import Collateral
        return Collateral.objects.filter(
            promocode_id=self.enterprise.promocode_id)

    @staticmethod
    def validate_referral_code(code):
        return Referral.objects.filter(code=code).exists()

    @staticmethod
    def validate_promo_code(code):
        return PromoCode.objects.filter(code=code).exists()

    @staticmethod
    def get_referral_details(code):
        # To Dos: Remove this
        referrals = Referral.objects.filter(code=code)
        if not referrals.exists():
            return {
                'user_type': Constants.DEFAULT_USER_TYPE,
                'enterprise_id': SubcriberEnterprise.objects.get(
                    name=Constants.DEFAULT_ENTERPRISE).id
            }
        referral = referrals.get()
        from earnings.models import Earning
        Earning.objects.create(
            user_id=referral.user.id, earning_type='referral', amount=100)
        return dict(
            enterprise_id=(
                referral.enterprise or SubcriberEnterprise.objects.get(
                    name=Constants.DEFAULT_ENTERPRISE)).id)

    @staticmethod
    def get_promo_code_details(code, name):
        promo_code = PromoCode.objects.get(code=code)
        enterprises = Enterprise.objects.filter(
            promocode=promo_code, enterprise_type='enterprise')
        if enterprises.exists():
            return dict(
                user_type='enterprise', enterprise_id=enterprises.get().id)
        enterprise = Enterprise.objects.create(name=name, promocode=promo_code)
        from product.models import Category, Company
        for category_id in Category.objects.values_list('id', flat=True):
            enterprise.categories.add(category_id)
        for company_id in Company.objects.values_list('id', flat=True):
            enterprise.companies.add(company_id)
        enterprise.save()
        return dict(
            user_type=enterprise.enterprise_type,
            enterprise_id=enterprise.id)

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
    enterprise_type = models.CharField(
        choices=get_choices(Constants.USER_TYPE), max_length=16,
        default=Constants.DEFAULT_USER_TYPE)
    companies = models.ManyToManyField('product.Company', blank=True)
    categories = models.ManyToManyField('product.Category', blank=True)
    hexa_code = models.CharField(max_length=8, default='#005db1')
    promocode = models.ForeignKey('users.PromoCode', on_delete=models.PROTECT)
    logo = models.ImageField(
        upload_to=Constants.ENTERPRISE_UPLOAD_PATH,
        default=Constants.DEFAULT_LOGO)
    commission = models.FloatField(default=0.0)

    def save(self, *args, **kwargs):
        try:
            current = self.__class__.objects.get(pk=self.id)
            if current.promocode != self.promocode:
                self.update_enterprise_type()
        except self.__class__.DoesNotExist:
            if self.promocode.code == 'OCOVR-1-3':
                self.enterprise_type = 'pos'
        super(self.__class__, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def update_enterprise_type(self):
        users = User.objects.filter(enterprise_id=self.id)
        if not users.exists():
            return
        user = users.get()
        if self.promocode.code == 'OCOVR-1-3':
            self.enterprise_type = user.user_type = 'pos'
        elif self.promocode.code == 'OCOVR-2-4':
            self.enterprise_type = user.user_type = 'subscriber'
        else:
            self.enterprise_type = user.user_type = 'enterprise'
        user.save()


class SubcriberEnterprise(BaseModel):
    name = models.CharField(
        max_length=64, default=Constants.DEFAULT_ENTERPRISE)
    companies = models.ManyToManyField('product.Company', blank=True)
    categories = models.ManyToManyField('product.Category', blank=True)
    hexa_code = models.CharField(max_length=8, default='#005db1')
    logo = models.ImageField(
        upload_to=Constants.ENTERPRISE_UPLOAD_PATH,
        default=Constants.DEFAULT_LOGO)
    person = GenericRelation(
        'users.User', related_query_name='subscriber_enterprise_user',
        object_id_field='enterprise_id')
    commission = models.FloatField(default=0.0)

    def __str__(self):
        return self.name


class AccountDetail(BaseModel):
    account = models.OneToOneField('users.Account', on_delete=models.CASCADE)
    agent_code = models.CharField(max_length=16, null=True, blank=True)
    branch_code = models.CharField(max_length=16, null=True, blank=True)
    designation = models.CharField(max_length=16, null=True, blank=True)
    channel = models.CharField(max_length=16, null=True, blank=True)
    status = models.CharField(max_length=32, null=True, blank=True)
    languages = ArrayField(
        models.CharField(max_length=16), default=list, blank=True, null=True)
    certifications = ArrayField(
        models.CharField(max_length=64), default=list, blank=True, null=True)
    qualifications = ArrayField(
        models.CharField(max_length=128), default=list, blank=True, null=True)
    short_description = models.TextField(null=True, blank=True)
    long_description = models.TextField(null=True, blank=True)


class PromoCode(BaseModel):
    code = models.CharField(max_length=16, unique=True)

    def __str__(self):
        return '%s' % (self.code)


class Referral(BaseModel):
    code = models.CharField(max_length=8, blank=True)
    reference_code = models.CharField(max_length=6, null=True, blank=True)
    user = models.OneToOneField(
        'users.User', null=True, blank=True, on_delete=models.CASCADE)


class KYCDocument(BaseModel):
    account = models.ForeignKey('users.Account', on_delete=models.CASCADE)
    document_type = models.CharField(
        choices=get_choices(Constants.KYC_DOC_TYPES), max_length=16)
    document_number = models.CharField(max_length=64)
    file = models.FileField(upload_to=get_kyc_upload_path)
    ignore = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        previous = self.__class__.objects.filter(
            document_type=self.document_type, account_id=self.id)
        if previous.exists():
            previous.update(ignore=True)
        super(self.__class__, self).save(*args, **kwargs)

    def __str__(self):
        return self.document_type


class BankAccount(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    branch = models.OneToOneField(
        'content.BankBranch', on_delete=models.CASCADE)
    account_no = models.CharField(max_length=32)
    default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        try:
            if self.default and BankAccount.objects.filter(
                    default=True).exists():
                self.default = False
        except self.__class__.DoesNotExist:
            self.__class__.objects.all().update(default=False)
            self.default = True
        super(BankAccount, self).save(*args, **kwargs)


class State(models.Model):
    name = models.CharField(max_length=128, db_index=True)

    def __str__(self):
        return self.name


class Pincode(models.Model):
    pincode = models.CharField(
        max_length=6, unique=True, db_index=True)
    city = models.CharField(max_length=64, db_index=True)
    state = models.ForeignKey(
        'users.State', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return '%s - %s(%s)' % (self.city, self.pincode, self.state.name)

    @classmethod
    def get_pincode(cls, pincode):
        pincodes = cls.objects.filter(pincode=pincode)
        if pincodes.exists():
            return pincodes.get()
        return None


class Address(BaseModel):
    flat_no = models.CharField(max_length=64, blank=True)
    street = models.CharField(max_length=128, blank=True)
    landmark = models.CharField(max_length=128, blank=True)
    pincode = models.ForeignKey('users.Pincode', on_delete=models.CASCADE)

    @property
    def full_address(self):
        return '%s %s %s %s'.strip() % (
            self.flat_no, self.street, self.landmark, self.pincode)

    def __str__(self):
        return self.full_address


class IPAddress(BaseModel):
    account = models.ForeignKey(
        'users.Account', on_delete=models.PROTECT, null=True, blank=True)
    ip_address = models.CharField(max_length=16)
    company_name = models.CharField(max_length=128)
    authentication_required = models.BooleanField(default=True)
    blocked = models.BooleanField(default=False)

    @classmethod
    def _get_whitelisted_networks(cls):
        return cls.objects.filter(
            blocked=False).values_list('ip_address', flat=True)


@receiver(post_save, sender=User, dispatch_uid="action%s" % str(now()))
def user_post_save(sender, instance, created, **kwargs):
    if created:
        # To Dos remove this
        from content.models import EnterprisePlaylist
        EnterprisePlaylist.objects.create(
            enterprise_id=instance.enterprise_id,
            playlist_id=Constants.DEFAULT_TRAINING_PLAYLIST_ID)
        EnterprisePlaylist.objects.create(
            enterprise_id=instance.enterprise_id,
            playlist_id=Constants.DEFAULT_MARKETING_PLAYLIST_ID)
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
        message = dict(
            message=(Constants.USER_CREATION_MESSAGE % (instance.phone_no)),
            type='sms')
        instance.send_notification(**message)
        AccountDetail.objects.create(account_id=instance.id)
