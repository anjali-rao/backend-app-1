# -*- coding: utf-8 -*-
from rest_framework import serializers

from django.contrib.auth.hashers import make_password
from django.core.cache import cache

from users.models import (
    User, Account, Enterprise, AccountDetail, Pincode,
    Address, BankAccount, BankBranch)

from earnings.serializers import EarningSerializer

from django.db import transaction

from utils import constants as Constants, genrate_random_string


class OTPGenrationSerializer(serializers.Serializer):
    phone_no = serializers.CharField(required=True)

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                Constants.INVALID_PHONE_NO)
        Account.send_otp(value)
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
    referral_code = serializers.CharField(required=False)
    fcm_id = serializers.CharField(required=False)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.CharField(required=True)
    cancelled_cheque = serializers.FileField(required=False)
    photo = serializers.FileField(required=False)
    manager_id = serializers.CharField(required=False)
    user_type = serializers.CharField(default='enterprise')

    def validate_password(self, value):
        return make_password(value)

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
        validated_data.update(User.get_referral_details(
            validated_data.get('referral_code')))
        account = self.get_account(validated_data)
        data = dict(
            account_id=account.id,
            user_type=validated_data['user_type'],
            enterprise_id=validated_data['enterprise_id'],
            manager_id=validated_data.get('manager_id'),
            is_active=True
        )
        self.instance = User.objects.create(**data)
        self.instance.generate_referral(validated_data.get('referral_code'))
        if any(x in validated_data.keys() for x in Constants.USER_FILE_UPLOAD):
            account.upload_docs(
                validated_data, set(validated_data).intersection(
                    set(Constants.USER_FILE_UPLOAD)))
        return self.instance

    def get_account(self, validated_data):
        validated_data['address_id'] = Address.objects.create(
            pincode_id=validated_data['pincode']).id
        acc = Account.get_account(validated_data['phone_no'])
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
            'photo', 'manager_id', 'user_type', 'fcm_id'
        )


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
    profile_pic = serializers.SerializerMethodField()

    def get_profile_pic(self, obj):
        photos = obj.document_set.filter(doc_type='photo')
        if photos.exists():
            return photos.latest('created').file.url
        return ''

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
    account = serializers.SerializerMethodField()
    enterprise = serializers.SerializerMethodField()
    available_users = serializers.SerializerMethodField()
    referral_code = serializers.ReadOnlyField(source='referral.referral_code')
    bank_details = serializers.SerializerMethodField()

    def get_account(self, obj):
        return AccountSerializer(obj.account).data

    def get_enterprise(self, obj):
        return EnterpriseSerializer(obj.enterprise).data

    def get_available_users(self, obj):
        return AvailableUserSerializer(
            User.objects.filter(account_id=obj.account_id), many=True).data

    def get_bank_details(self, obj):
        return BankAccountSerializer(
            obj.bankaccount_set.all(), many=True).data

    class Meta:
        model = User
        fields = (
            'id', 'user_type', 'account', 'enterprise', 'available_users',
            'rating', 'referral_code', 'bank_details'
        )


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
    def response(self):
        return {
            'authorization': self.get_user().get_authorization_key(),
            'message': Constants.AUTHORIZATION_GENERATED,
            'details': UserSerializer(self.get_user()).data,
        }


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
    cancelled_cheque = serializers.FileField(required=False)
    photo = serializers.FileField(required=False)
    manager_id = serializers.CharField(required=False)
    street = serializers.CharField(required=False)
    flat_no = serializers.CharField(required=False)
    landmark = serializers.CharField(required=False)

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
            x in validated_data.keys() for x in Constants.USER_FILE_UPLOAD
        ):
            self.initial_data = acc.upload_docs(
                validated_data, set(validated_data).intersection(
                    set(Constants.USER_FILE_UPLOAD)))

    def get_address_id(self, acc, validated_data):
        if validated_data['pincode_id'] != acc.address.pincode_id:
            address = Address.objects.create(
                pincode_id=Pincode.get_pincode(
                    validated_data['pincode']).id).id
        else:
            address = acc.address_id
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
            'flat_no', 'landmark'
        )


class UserEarningSerializer(serializers.ModelSerializer):
    total_policies = serializers.SerializerMethodField()
    total_earning = serializers.SerializerMethodField()
    total_premium = serializers.SerializerMethodField()
    earning_details = serializers.SerializerMethodField()

    def get_total_policies(self, obj):
        return obj.get_policies().count()

    def get_total_earning(self, obj):
        return obj.get_earnings()

    def get_total_premium(self, obj):
        return sum(obj.get_policies().values_list(
            'application__premium', flat=True))

    def get_earning_details(self, obj):
        return EarningSerializer(
            obj.earning_set.filter(ignore=False), many=True).data

    class Meta:
        model = User
        fields = (
            'total_premium', 'total_earning', 'total_policies',
            'earning_details')


class UserDetailSerializer(serializers.ModelSerializer):
    certifications = serializers.SerializerMethodField()
    agent_id = serializers.UUIDField(source='id')
    categories = serializers.SerializerMethodField()
    phone_no = serializers.ReadOnlyField(source='account.phone_no')
    name = serializers.ReadOnlyField(source='account.get_full_name')
    pan_no = serializers.ReadOnlyField(source='account.pan_no')
    rating = serializers.ReadOnlyField(source='account.user.rating', default=4)
    bank_details = serializers.SerializerMethodField()
    short_description = serializers.ReadOnlyField(
        source='account.accountdetail.short_description', default='')
    long_description = serializers.ReadOnlyField(
        source='account.accountdetail.long_description', default='')
    profile_pic = serializers.FileField(source='account.profile_pic')
    product_sold = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

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
            'rating', 'bank_details'
        )
