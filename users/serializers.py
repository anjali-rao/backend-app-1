from rest_framework import serializers

from django.contrib.auth.hashers import make_password
from django.core.cache import cache

from users.models import User, Account, Enterprise, AccountDetails, Pincode

from utils import constants, genrate_random_string


class OTPGenrationSerializer(serializers.Serializer):
    phone_no = serializers.CharField(required=True)

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                constants.INVALID_PHONE_NO)
        Account.send_otp(value)
        return value

    @property
    def response(self):
        return {
            'message': constants.OTP_GENERATED,
        }


class OTPVerificationSerializer(serializers.Serializer):
    phone_no = serializers.CharField(required=True)
    otp = serializers.IntegerField(required=True)

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                constants.INVALID_PHONE_NO)
        return value

    def validate_otp(self, value):
        if not Account.verify_otp(
                self.initial_data.get('phone_no'), value):
            raise serializers.ValidationError(
                constants.OTP_VALIDATION_FAILED)
        return value

    def get_transaction_id(self):
        txn_id = genrate_random_string(12)
        cache.set(
            'TXN:%s' % self.validated_data['phone_no'], txn_id,
            constants.TRANSACTION_TTL)
        return txn_id

    @property
    def response(self):
        cache.delete(self.validated_data['phone_no'])
        return {
            'transaction_id': self.get_transaction_id(),
            'message': constants.OTP_SUCCESS
        }


class CreateUserSerializer(serializers.ModelSerializer):
    pincode = serializers.CharField(
        required=False, allow_blank=True, max_length=6)
    pan_no = serializers.CharField(
        required=False, allow_blank=True, max_length=10)
    phone_no = serializers.CharField(required=True, max_length=10)
    transaction_id = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    referral_code = serializers.CharField(required=False)
    referral_reference = serializers.CharField(required=False)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.CharField(required=True)

    def validate_password(self, value):
        return make_password(value)

    def validate_referral_code(self, value):
        validate_referral = User.validate_referral_code(value)
        if not validate_referral:
            raise serializers.ValidationError(
                constants.REFERRAL_CODE_EXCEPTION)
        return value

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                constants.INVALID_PHONE_NO)
        return value

    def validate_transaction_id(self, value):
        if not cache.get(
                'TXN:%s' % self.initial_data.get('phone_no')) == value:
            raise serializers.ValidationError(
                constants.INVALID_TRANSACTION_ID)
        return value

    def create(self, validated_data):
        validated_data.update(User.get_referral_details(
            validated_data.get('referral_code')))
        account = self.get_account(validated_data)
        data = {
            'account_id': account.id,
            'user_type': validated_data['user_type'],
            'enterprise_id': validated_data['enterprise_id'],
            'is_active': True
        }
        instance = User.objects.create(**data)
        instance.generate_referral()
        return instance

    def get_account(self, validated_data):
        acc = Account.get_account(validated_data['phone_no'])
        for field_name in constants.ACCOUNT_CREATION_FIELDS:
            setattr(acc, field_name, validated_data.get(field_name))
        acc.save()
        return acc

    @property
    def response(self):
        cache.delete('TXN:%s' % self.validated_data['phone_no'])
        return {
            'phone_no': self.validated_data['phone_no'],
            'message': constants.USER_CREATED_SUCESS
        }

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'password',
            'referral_code', 'referral_reference', 'user_type', 'pincode',
            'pan_no', 'phone_no', 'transaction_id'
        )


class AccountSerializer(serializers.ModelSerializer):
    pincode =serializers.SerializerMethodField()

    def get_pincode(self, obj):

        if obj.pincode:
            return PincodeSerializer(obj.pincode).data
        else:
            return {}

    class Meta:
        model = Account
        fields = (
            'id', 'first_name', 'last_name', 'email', 'phone_no',
            'gender', 'address', 'pincode'
        )


class EnterpriseSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    def get_logo(self, obj):
        from goplannr.settings import BASE_HOST
        return BASE_HOST + obj.logo.url

    class Meta:
        model = Enterprise
        fields = ('id', 'name', 'logo', 'hexa_code')


class AvailableUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.enterprise.name

    class Meta:
        model = User
        fields = ('id', 'name')


class UserSerializer(serializers.ModelSerializer):
    account = serializers.SerializerMethodField()
    enterprise = serializers.SerializerMethodField()
    available_users = serializers.SerializerMethodField()

    def get_account(self, obj):
        return AccountSerializer(obj.account).data

    def get_enterprise(self, obj):
        return EnterpriseSerializer(obj.enterprise).data

    def get_available_users(self, obj):
        return AvailableUserSerializer(
            User.objects.filter(account_id=obj.account_id), many=True).data

    class Meta:
        model = User
        fields = (
            'id', 'user_type', 'account', 'enterprise', 'available_users'
        )


class AuthorizationSerializer(serializers.Serializer):
    phone_no = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    is_active = serializers.BooleanField(default=True)

    def validate_phone_no(self, value):
        accounts = Account.objects.filter(phone_no=value)
        if not accounts.exists():
            raise serializers.ValidationError(
                constants.INVALID_PHONE_NO)
        return value

    def validate_password(self, value):
        accounts = Account.objects.filter(
            phone_no=self.initial_data.get('phone_no'))
        if not accounts.exists():
            raise serializers.ValidationError(
                constants.INVALID_PHONE_NO)
        account = accounts.get()
        if not account.check_password(value):
            raise serializers.ValidationError(
                constants.INVALID_PASSWORD)
        return value

    def validate_is_active(self, value):
        accounts = Account.objects.filter(
            phone_no=self.initial_data.get('phone_no'))
        if accounts.exists() and not accounts.get().get_default_user():
            raise serializers.ValidationError(
                constants.ACCOUNT_DISABLED)
        return value

    def get_user(self):
        account = Account.objects.get(
            phone_no=self.validated_data.get('phone_no'))
        return account.get_default_user()

    @property
    def response(self):
        return {
            'authorization': self.get_user().get_authorization_key(),
            'message': constants.AUTHORIZATION_GENERATED,
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
                constants.INVALID_PHONE_NO)
        return value

    def validate_transaction_id(self, value):
        accounts = Account.objects.filter(
            phone_no=self.initial_data.get('phone_no'))
        if not accounts.exists() or not cache.get(
                'TXN:%s' % accounts.get().phone_no) == value:
            raise serializers.ValidationError(
                constants.INVALID_TRANSACTION_ID)
        return value

    def get_account(self):
        return Account.objects.get(phone_no=self.validated_data['phone_no'])

    @property
    def response(self):
        account = self.get_account()
        account.set_password(self.validated_data['new_password'])
        account.save()
        message = {
            'message': constants.USER_PASSWORD_CHANGE, 'type': 'sms'
        }
        account.send_notification(**message)
        cache.delete('TXN:%s' % self.validated_data.get('phone_no'))
        return {
            'message': constants.PASSWORD_CHANGED
        }


class AccountDetailsSerializers(serializers.ModelSerializer):

    class Meta:
        model = AccountDetails
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
    state = serializers.SerializerMethodField()

    def get_state(self, obj):
        return obj.state.name

    class Meta:
        model = Pincode
        fields = ('pincode', 'city', 'state')
