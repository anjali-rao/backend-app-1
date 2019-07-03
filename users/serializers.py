# -*- coding: utf-8 -*-
from rest_framework import serializers

from django.contrib.auth.hashers import make_password
from django.core.cache import cache

from users.models import (
    User, Account, Enterprise, AccountDetail, Pincode,
    Address, BankAccount)
from content.models import BankBranch

from earnings.serializers import EarningSerializer
from crm.serializers import LeadSerializer, Lead, ClientSerializer

from django.db import transaction

from utils import constants as Constants, genrate_random_string


class OTPGenrationSerializer(serializers.Serializer):
    phone_no = serializers.CharField(required=True)

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                Constants.INVALID_PHONE_NO)
        Account.send_otp('OTP:%s' % value, value)
        return value

    @property
    def response(self):
        return {
            'message': Constants.OTP_GENERATED,
        }


class OTPVerificationSerializer(serializers.Serializer):
    phone_no = serializers.CharField(required=True)
    otp = serializers.IntegerField(required=True)

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                Constants.INVALID_PHONE_NO)
        return value

    def validate_otp(self, value):
        if not Account.verify_otp(
                self.initial_data.get('phone_no'), value):
            raise serializers.ValidationError(
                Constants.OTP_VALIDATION_FAILED)
        return value

    def get_transaction_id(self):
        txn_id = genrate_random_string(12)
        cache.set(
            'TXN:%s' % self.validated_data['phone_no'], txn_id,
            Constants.TRANSACTION_TTL)
        return txn_id

    @property
    def response(self):
        cache.delete(self.validated_data['phone_no'])
        return {
            'transaction_id': self.get_transaction_id(),
            'message': Constants.OTP_SUCCESS
        }


class CreateUserSerializer(serializers.ModelSerializer):
    pincode = serializers.CharField(
        required=True, allow_blank=True, min_length=6, max_length=6)
    pan_no = serializers.CharField(
        required=False, allow_blank=True, max_length=10)
    phone_no = serializers.CharField(required=True, max_length=10)
    transaction_id = serializers.CharField(required=True)
    password = serializers.CharField(required=False)
    promo_code = serializers.CharField(required=False, default='OCOVR-2-4')
    referral_code = serializers.CharField(required=False)
    fcm_id = serializers.CharField(required=False)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.CharField(required=True)
    manager_id = serializers.CharField(required=False)
    user_type = serializers.CharField(default=Constants.DEFAULT_USER_TYPE)
    photo = serializers.FileField(required=False)
    pancard = serializers.FileField(required=False)
    cancelled_cheque = serializers.FileField(required=False)
    aadhaar_card = serializers.FileField(required=False)
    educational_document = serializers.FileField(required=False)
    driving_license = serializers.FileField(required=False)

    def validate_password(self, value):
        return make_password(value)

    def validate_promo_code(self, value):
        validate_referral = User.validate_promo_code(value)
        if not validate_referral:
            raise serializers.ValidationError(
                Constants.INVALID_PROMO_CODE)
        return value

    def validate_referral_code(self, value):
        validate_referral = User.validate_referral_code(value)
        if not validate_referral:
            raise serializers.ValidationError(
                Constants.REFERRAL_CODE_EXCEPTION)
        return value

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                Constants.INVALID_PHONE_NO)
        return value

    def validate_transaction_id(self, value):
        if not cache.get(
                'TXN:%s' % self.initial_data.get('phone_no')) == value:
            raise serializers.ValidationError(
                Constants.INVALID_TRANSACTION_ID)
        return value

    def validate_pincode(self, value):
        pincodes = Pincode.objects.filter(pincode=value)
        if not pincodes.exists():
            raise serializers.ValidationError(
                Constants.INVALID_PINCODE)
        return pincodes.get().id

    def create(self, validated_data):
        account = self.get_account(validated_data)
        validated_data.update(User.get_promo_code_details(
            validated_data['promo_code'], account.get_full_name()))
        data = dict(
            account_id=account.id, is_active=True,
            user_type=validated_data['user_type'],
            enterprise_id=validated_data['enterprise_id'],
            manager_id=validated_data.get('manager_id'))
        self.instance = User.objects.create(**data)
        self.instance.generate_referral(validated_data.get('referral_code'))
        if any(x in validated_data.keys() for x in Constants.KYC_DOC_TYPES):
            account.upload_docs(
                validated_data, set(validated_data).intersection(
                    set(Constants.KYC_DOC_TYPES)))
        return self.instance

    def get_account(self, validated_data):
        validated_data['address_id'] = Address.objects.create(
            pincode_id=validated_data['pincode']).id
        acc = Account.get_account(
            validated_data['phone_no'], validated_data['first_name'],
            validated_data['last_name'])
        for field_name in Constants.ACCOUNT_CREATION_FIELDS:
            setattr(acc, field_name, validated_data.get(field_name))
        acc.save()
        return acc

    @property
    def response(self):
        cache.delete('TXN:%s' % self.validated_data['phone_no'])
        return {
            'phone_no': self.validated_data['phone_no'],
            'message': Constants.USER_CREATED_SUCESS,
            'user_id': self.instance.id
        }

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'password',
            'referral_code', 'user_type', 'pincode', 'pan_no',
            'phone_no', 'transaction_id', 'cancelled_cheque',
            'photo', 'manager_id', 'user_type', 'fcm_id', 'promo_code',
            'pancard', 'cancelled_cheque', 'aadhaar_card',
            'educational_document', 'driving_license')


class AccountSerializer(serializers.ModelSerializer):
    account_id = serializers.ReadOnlyField(source='id')
    address = serializers.ReadOnlyField(
        source='address.full_address', default=None)
    pincode = serializers.ReadOnlyField(
        source='address.pincode.pincode', default=None)
    city = serializers.ReadOnlyField(
        source='address.pincode.city', default=None)
    state = serializers.ReadOnlyField(
        source='address.pincode.state.name', default=None)
    profile_pic = serializers.FileField(
        source='account.profile_pic', default='')

    class Meta:
        model = Account
        fields = (
            'account_id', 'first_name', 'last_name', 'email', 'phone_no',
            'gender', 'address', 'pincode', 'city', 'state', 'profile_pic'
        )


class EnterpriseSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    def get_logo(self, obj):
        from goplannr.settings import DEBUG
        return (Constants.DEBUG_HOST if DEBUG else '') + obj.logo.url

    class Meta:
        model = Enterprise
        fields = ('id', 'name', 'logo', 'hexa_code')


class AvailableUserSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='enterprise.name')

    class Meta:
        model = User
        fields = ('id', 'name')


class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.ReadOnlyField(source='id')
    first_name = serializers.ReadOnlyField(source='account.first_name')
    last_name = serializers.ReadOnlyField(source='account.last_name')
    email = serializers.ReadOnlyField(source='account.email')
    phone_no = serializers.ReadOnlyField(source='account.phone_no')
    gender = serializers.ReadOnlyField(source='account.gender', default='')
    flat_no = serializers.ReadOnlyField(
        source='account.address.flat_no', default='')
    street = serializers.ReadOnlyField(
        source='account.address.street', default='')
    city = serializers.ReadOnlyField(
        source='account.address.pincode.city', default='')
    state = serializers.ReadOnlyField(
        source='account.address.pincode.state.name', default='')
    pincode = serializers.ReadOnlyField(
        source='account.address.pincode.pincode', default='')
    profile_pic = serializers.FileField(
        source='account.profile_pic', default='')
    referral_code = serializers.ReadOnlyField(source='referral.code')
    profile_url = serializers.SerializerMethodField()

    def get_profile_url(self, obj):
        return 'https://advisor.onecover.in/%s' % obj.account.username

    class Meta:
        model = User
        fields = (
            'user_id', 'first_name', 'last_name', 'email', 'phone_no',
            'gender', 'flat_no', 'street', 'city', 'state', 'pincode',
            'profile_pic', 'rating', 'referral_code', 'profile_url')


class AuthorizationSerializer(serializers.Serializer):
    phone_no = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    is_active = serializers.BooleanField(default=True)

    def validate_phone_no(self, value):
        accounts = Account.objects.filter(phone_no=value)
        if not accounts.exists():
            raise serializers.ValidationError(
                Constants.INVALID_PHONE_NO)
        return value

    def validate_password(self, value):
        accounts = Account.objects.filter(
            phone_no=self.initial_data.get('phone_no'))
        if accounts.exists() and not accounts.get().password:
            raise serializers.ValidationError(Constants.PASSWORD_NOT_SET)
        if not accounts.exists() or not accounts.get().check_password(value):
            raise serializers.ValidationError(
                Constants.INVALID_PASSWORD)
        return value

    def validate_is_active(self, value):
        accounts = Account.objects.filter(
            phone_no=self.initial_data.get('phone_no'))
        if accounts.exists() and not accounts.get().get_default_user():
            raise serializers.ValidationError(
                Constants.ACCOUNT_DISABLED)
        return value

    def get_user(self):
        account = Account.objects.get(
            phone_no=self.validated_data.get('phone_no'))
        return account.get_default_user()

    @property
    def data(self):
        user = self.get_user()
        self._data = dict(
            authorization=self.get_user().get_authorization_key(),
            message=Constants.AUTHORIZATION_GENERATED,
            details=UserSerializer(user).data,
            enterprise=EnterpriseSerializer(user.enterprise).data,
            rules=user.get_rules(),
            categories=user.get_categories())
        return self._data


class ChangePasswordSerializer(serializers.Serializer):
    phone_no = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    transaction_id = serializers.CharField(required=True)

    def validate_phone_no(self, value):
        accounts = Account.objects.filter(phone_no=value)
        if not accounts.exists():
            raise serializers.ValidationError(
                Constants.INVALID_PHONE_NO)
        return value

    def validate_transaction_id(self, value):
        accounts = Account.objects.filter(
            phone_no=self.initial_data.get('phone_no'))
        if not accounts.exists() or not cache.get(
                'TXN:%s' % accounts.get().phone_no) == value:
            raise serializers.ValidationError(
                Constants.INVALID_TRANSACTION_ID)
        return value

    def get_account(self):
        return Account.objects.get(phone_no=self.validated_data['phone_no'])

    @property
    def response(self):
        account = self.get_account()
        account.set_password(self.validated_data['new_password'])
        account.save()
        account.send_notification(**dict(
            message=Constants.USER_PASSWORD_CHANGE, type='sms'))
        cache.delete('TXN:%s' % self.validated_data.get('phone_no'))
        return {
            'message': Constants.PASSWORD_CHANGED
        }


class AccountDetailsSerializers(serializers.ModelSerializer):

    class Meta:
        model = AccountDetail
        fields = '__all__'


class AccountSearchSerializers(serializers.ModelSerializer):
    account = serializers.SerializerMethodField()

    def get_account(self, obj):
        return AccountSerializer(obj.account).data

    class Meta:
        model = User
        fields = (
            'account',
        )


class PincodeSerializer(serializers.ModelSerializer):
    state = serializers.ReadOnlyField(source='state.name')

    class Meta:
        model = Pincode
        fields = ('pincode', 'city', 'state')


class BankAccountSerializer(serializers.ModelSerializer):
    bank_name = serializers.ReadOnlyField(source='branch.bank.name')
    branch = serializers.ReadOnlyField(source='branch.branch_name')
    ifsc = serializers.ReadOnlyField(source='branch.ifsc')
    city = serializers.ReadOnlyField(source='branch.city')

    class Meta:
        model = BankAccount
        fields = (
            'account_no', 'bank_name', 'branch', 'ifsc', 'city',
            'default', 'is_active')


class CreateBranch(serializers.ModelSerializer):

    class Meta:
        model = BankBranch
        fields = ('bank_id', 'branch_name', 'ifsc', 'micr', 'city')


class CreateBankAccount(serializers.ModelSerializer):

    class Meta:
        model = BankAccount
        fields = ('user_id', 'branch_id', 'account_no')


class UpdateUserSerializer(serializers.ModelSerializer):
    pincode = serializers.CharField(
        required=True, allow_blank=True, min_length=6, max_length=6)
    pan_no = serializers.CharField(
        required=False, allow_blank=True, max_length=10)
    password = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    manager_id = serializers.CharField(required=False)
    street = serializers.CharField(required=False)
    flat_no = serializers.CharField(required=False)
    landmark = serializers.CharField(required=False)
    photo = serializers.FileField(required=False)
    pancard = serializers.FileField(required=False)
    cancelled_cheque = serializers.FileField(required=False)
    aadhaar_card = serializers.FileField(required=False)
    educational_document = serializers.FileField(required=False)
    driving_license = serializers.FileField(required=False)

    def validate_password(self, value):
        return make_password(value)

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                Constants.INVALID_PHONE_NO)
        return value

    def validate_pincode(self, value):
        pincodes = Pincode.objects.filter(pincode=value)
        if not pincodes.exists():
            raise serializers.ValidationError(
                Constants.INVALID_PINCODE)
        return pincodes.get().id

    def save(self, **kwargs):
        with transaction.atomic():
            self.instance = super(
                UpdateUserSerializer, self).save(**kwargs)
            self.update_account(**kwargs)

    def update_account(self, **kwargs):
        validated_data = dict(
            list(self.validated_data.items()) + list(kwargs.items()))
        acc = self.instance.account
        address_fields = Constants.ADDRESS_UPDATE_FIELDS + ['pincode']
        if any(x in validated_data.keys() for x in address_fields):
            acc.address_id = self.get_address_id(acc, validated_data)
        for field_name in Constants.ACCOUNT_UPDATION_FIELDS:
            setattr(acc, field_name, validated_data.get(
                field_name, getattr(acc, field_name)))
        acc.save()
        if any(
            x in validated_data.keys() for x in Constants.KYC_DOC_TYPES
        ):
            self.initial_data = acc.upload_docs(
                validated_data, set(validated_data).intersection(
                    set(Constants.KYC_DOC_TYPES)))

    def get_address_id(self, acc, validated_data):
        if validated_data['pincode'] != acc.address.pincode_id:
            address = Address.objects.create(
                pincode_id=validated_data['pincode'])
        else:
            address = acc.address
        validated_data['address_id'] = address.id
        for field_name in Constants.ADDRESS_UPDATE_FIELDS:
            setattr(address, field_name, validated_data.get(
                field_name, getattr(address, field_name)))
        address.save()
        return address.id

    @property
    def data(self):
        self._data = dict(
            message='User updated successfully',
            updated_fields=self.initial_data)
        return self._data

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'password', 'manager_id',
            'pincode', 'pan_no', 'cancelled_cheque', 'photo', 'street',
            'flat_no', 'landmark', 'pancard', 'aadhaar_card',
            'educational_document', 'driving_license')


class UserEarningSerializer(serializers.ModelSerializer):
    total_policies = serializers.SerializerMethodField()
    total_earning = serializers.SerializerMethodField()
    total_premium = serializers.SerializerMethodField()
    earning_details = serializers.SerializerMethodField()

    def get_total_policies(self, obj):
        return obj.get_policies().count()

    def get_total_earning(self, obj):
        return round(obj.get_earnings(), 2)

    def get_total_premium(self, obj):
        return round(sum(obj.get_policies().values_list(
            'application__premium', flat=True)), 2)

    def get_earning_details(self, obj):
        return EarningSerializer(
            obj.earning_set.filter(ignore=False), many=True).data

    class Meta:
        model = User
        fields = (
            'total_premium', 'total_earning', 'total_policies',
            'earning_details')


class UserDetailSerializerV2(serializers.ModelSerializer):
    certifications = serializers.SerializerMethodField()
    agent_id = serializers.UUIDField(source='id')
    categories = serializers.SerializerMethodField()
    phone_no = serializers.ReadOnlyField(source='account.phone_no')
    first_name = serializers.ReadOnlyField(source='account.first_name')
    last_name = serializers.ReadOnlyField(source='account.last_name')
    name = serializers.ReadOnlyField(source='account.get_full_name')
    pan_no = serializers.ReadOnlyField(source='account.pan_no')
    bank_details = serializers.SerializerMethodField()
    short_description = serializers.ReadOnlyField(
        source='account.accountdetail.short_description', default='')
    long_description = serializers.ReadOnlyField(
        source='account.accountdetail.long_description', default='')
    profile_pic = serializers.FileField(
        source='account.profile_pic', default='')
    product_sold = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    email = serializers.ReadOnlyField(source='account.email', default='')

    def get_certifications(self, obj):
        data = list()
        for certificate in obj.account.accountdetail.certifications:
            data.append(dict(
                certificate=certificate,
                image='/static/img/certificate.jpg'))
        return data

    def get_categories(self, obj):
        data = obj.get_categories()
        for category in data:
            category['icon_class'] = 'fa'
        return data

    def get_location(self, obj):
        if obj.account.address:
            return PincodeSerializer(obj.account.address.pincode).data
        return dict(state='', city='', pincode='')

    def get_product_sold(self, obj):
        return [dict(
            name='Health Guard', company='Bajaj Allianz GIC',
            logo='http://localhost:8000/media/company/Bajaj_Allianz.png',
            variant_name='Health Guard')]

    def get_bank_details(self, obj):
        return BankAccountSerializer(
            obj.bankaccount_set.all(), many=True).data

    class Meta:
        model = User
        fields = (
            'agent_id', 'phone_no', 'name', 'categories', 'profile_pic',
            'certifications', 'location', 'short_description',
            'long_description', 'product_sold', 'user_type', 'pan_no',
            'bank_details', 'email', 'first_name', 'last_name'
        )


class UserDetailSerializerV3(serializers.ModelSerializer):
    details = serializers.SerializerMethodField()
    enterprise = EnterpriseSerializer(read_only=True)
    rules = serializers.ReadOnlyField(source='get_rules')
    categories = serializers.ReadOnlyField(source='get_categories')

    def get_details(self, obj):
        return UserSerializer(obj).data

    class Meta:
        model = User
        fields = ('details', 'enterprise', 'rules', 'categories')


class ContactSerializers(serializers.ModelSerializer):
    leads = serializers.SerializerMethodField()
    clients = serializers.SerializerMethodField()

    def get_leads(self, obj):
        return LeadSerializer(
            Lead.objects.filter(
                user_id=obj.id, is_client=False,
                ignore=False).exclude(contact=None),
            many=True).data

    def get_clients(self, obj):
        return ClientSerializer(
            Lead.objects.filter(
                user_id=obj.id, ignore=False, is_client=True
            ).exclude(contact=None), many=True).data

    class Meta:
        model = User
        fields = ('leads', 'clients')


class AdvisorSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='account.get_full_name')
    phone_no = serializers.ReadOnlyField(source='account.phone_no')
    email_id = serializers.ReadOnlyField(source='account.email')
    profile_pic = serializers.FileField(
        source='account.profile_pic', default='')
    pincode = serializers.ReadOnlyField(
        source='account.address.pincode.pincode', default='')
    city = serializers.ReadOnlyField(
        source='account.address.pincode.city', default='')
    state = serializers.ReadOnlyField(
        source='account.address.pincode.state.name', default='')
    products = serializers.SerializerMethodField()

    def get_products(self, obj):
        data = list()
        companies = obj.get_companies()
        from product.serializers import BrandSerializers
        for category in obj.enterprise.categories.filter(is_active=True):
            data.append(dict(
                category=category.name,
                brands=BrandSerializers(
                    companies.filter(
                        categories__in=[category.id]), many=True).data))
        return data

    class Meta:
        model = User
        fields = (
            'name', 'phone_no', 'email_id', 'profile_pic', 'pincode', 'city',
            'state', 'products')


class SendSMSSerializer(serializers.Serializer):
    phone_no = serializers.CharField(required=True)
    message = serializers.CharField(required=True)

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                Constants.INVALID_PHONE_NO)
        return value

    def send_sms(self):
        from users.tasks import send_sms
        send_sms(
            self.validated_data['phone_no'],
            self.validated_data['message'])

    @property
    def data(self):
        return dict(message='Message send successfully.')
