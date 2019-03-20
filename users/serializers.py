from rest_framework import serializers

from django.contrib.auth.hashers import make_password
from django.core.cache import cache

from users.models import User, Account, Enterprise
from utils import constants, genrate_random_string


class OTPGenrationSerializer(serializers.Serializer):
    phone_no = serializers.CharField(required=True)

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                constants.INVALID_PHONE_NO)
        User.send_otp(value)
        return value

    @property
    def response(self):
        return {
            'message': constants.OTP_GENERATED
        }


class ForgotPasswordOTPSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)

    def validate_username(self, value):
        users = User.objects.filter(username=value)
        if not users.exists():
            raise serializers.ValidationError(
                constants.INVALID_USERNAME)
        user = users.get()
        User.send_otp(user.account.phone_no)
        return value

    @property
    def response(self):
        user = User.objects.get(username=self.validated_data['username'])
        return {
            'message': constants.OTP_GENERATED,
            'phone_no': user.account.phone_no
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
        if not User.verify_otp(
                self.initial_data['phone_no'], value):
            raise serializers.ValidationError(
                constants.OTP_VALIDATION_FAILED)
        return value

    @property
    def response(self):
        return {
            'transaction_id': self.get_transaction_id(),
            'message': constants.OTP_SUCCESS
        }

    def get_transaction_id(self):
        txn_id = genrate_random_string(12)
        cache.set(self.data['phone_no'], txn_id, constants.TRANSACTION_TTL)
        return txn_id


class CreateUserSerializer(serializers.ModelSerializer):
    pincode = serializers.CharField(
        required=False, allow_blank=True, max_length=6)
    pan_no = serializers.CharField(
        required=False, allow_blank=True, max_length=10)
    phone_no = serializers.CharField(required=True)
    transaction_id = serializers.CharField(required=True)

    def validate_password(self, value):
        return make_password(value)

    def validate_referral_code(self, value):
        if not User.validate_referral_code(value):
            raise serializers.ValidationError(
                constants.REFERRAL_CODE_EXCEPTION)
        return value

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                constants.INVALID_PHONE_NO)
        return value

    def validate_transaction_id(self, value):
        if not cache.get(self.initial_data.get('phone_no')) == value:
            raise serializers.ValidationError(
                constants.INVALID_TRANSACTION_ID)
        return value

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email', 'password',
            'referral_code', 'referral_reference', 'user_type', 'pincode',
            'pan_no', 'phone_no', 'transaction_id'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        data = dict()
        for key in validated_data.iterkeys():
            if key in constants.USER_CREATION_FIELDS:
                data[key] = validated_data[key]
        data.update({
            'enterprise_id': self.get_enterprise_id(validated_data),
            'account_id': self.get_or_create_account(validated_data).id,
            'username': User.generate_username()
        })
        self.validated_data['username'] = data['username']
        instance = User.objects.create(**data)
        instance.referral_reference = validated_data.get('referral_reference')
        instance.generate_referral_code()
        # need to followed up latter: hriks Ref: Keep
        instance.is_active = True
        instance.save()
        return instance

    def get_or_create_account(self, validated_data):
        acc, created = Account.objects.get_or_create(
            phone_no=validated_data['phone_no'])
        acc.pincode = validated_data.get('pincode')
        acc.pan_no = validated_data.get('pan_no')
        acc.save()
        return acc

    def get_enterprise_id(self, validated_data):
        # To Dos: Logic for assigning enterprise
        return Enterprise.objects.get(name=constants.DEFAULT_ENTERPRISE).id

    def get_user(self):
        return User.objects.get(username=self.validated_data['username'])

    @property
    def response(self):
        return {
            'username': self.get_user().username,
            'phone_no': self.get_user().account.phone_no,
            'message': constants.USER_CREATED_SUCESS
        }


class AccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = '__all__'


class EnterpriseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Enterprise
        fields = ('id', 'name', 'logo', 'hexa_code')


class UserSerializer(serializers.ModelSerializer):
    account = serializers.SerializerMethodField()
    enterprise = serializers.SerializerMethodField()

    def get_account(self, obj):
        return AccountSerializer(obj.account).data

    def get_enterprise(self, obj):
        return EnterpriseSerializer(obj.enterprise).data

    class Meta:
        model = User
        fields = (
            'id', 'username', 'user_type', 'email',
            'is_active', 'account', 'enterprise'
        )


class AuthorizationSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    is_active = serializers.BooleanField(default=True)

    def validate_username(self, value):
        users = User.objects.filter(username=value)
        if not users.exists():
            raise serializers.ValidationError(
                constants.INVALID_USERNAME)
        return value

    def validate_password(self, value):
        users = User.objects.filter(username=self.initial_data.get('username'))
        if not users.exists():
            raise serializers.ValidationError(
                constants.INVALID_USERNAME)
        user = users.get()
        if not user.check_password(value):
            raise serializers.ValidationError(
                constants.INVALID_PASSWORD)
        return value

    def validate_is_active(self, value):
        users = User.objects.filter(username=self.initial_data.get('username'))
        if users.exists() and not users[0].is_active:
            raise serializers.ValidationError(
                constants.ACCOUNT_DISABLED)
        return value

    def get_user(self):
        return User.objects.get(username=self.validated_data['username'])

    @property
    def response(self):
        return {
            'authorization': self.get_user().get_authorization_key(),
            'username': self.validated_data['username'],
            'message': constants.AUTHORIZATION_GENERATED,
            'details': UserSerializer(self.get_user()).data,
        }


class ChangePasswordSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    transaction_id = serializers.CharField(required=True)

    def validate_username(self, value):
        users = User.objects.filter(username=value)
        if not users.exists():
            raise serializers.ValidationError(
                constants.INVALID_USERNAME)
#        user = users.get()
#        if user.account.phone_no != self.initial_data.get('phone_no'):
#            raise serializers.ValidationError(
#                constants.INVALID_USERNAME_PHONE_COMBINATION)
        return value

    def validate_phone_no(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError(
                constants.INVALID_PHONE_NO)
        return value

    def validate_transaction_id(self, value):
        users = User.objects.filter(username=self.initial_data.get('username'))
        if not cache.get(users.get().account.phone_no) == value:
            raise serializers.ValidationError(
                constants.INVALID_TRANSACTION_ID)
        return value

    def get_user(self):
        return User.objects.get(username=self.validated_data['username'])

    @property
    def response(self):
        user = self.get_user()
        user.set_password(self.validated_data['new_password'])
        user.save()
        return {
            'message': constants.PASSWORD_CHANGED
        }
