from rest_framework import serializers

from django.contrib.auth.hashers import make_password

from users.models import User, Account
from utils import constants


class CreateUserSerializer(serializers.ModelSerializer):
    pincode = serializers.CharField(
        required=False, allow_blank=True, max_length=6)
    pan_no = serializers.CharField(
        required=False, allow_blank=True, max_length=10)
    phone_no = serializers.CharField(required=True)

    def validate_username(self, value):
        return value.lower()

    def validate_password(self, value):
        return make_password(value)

    def validate_referral_code(self, value):
        if not User.validate_referral_code(value):
            raise serializers.ValidationError(
                constants.REFERRAL_CODE_EXCEPTION)
        return value

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 'password',
            'referral_code', 'referral_reference', 'user_type', 'pincode',
            'pan_no', 'phone_no'
        )
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        data = dict()
        for key in validated_data.iterkeys():
            if key in constants.USER_CREATION_FIELDS:
                data[key] = validated_data[key]
        instance = User.objects.create(**data)
        instance.account = self.get_or_create_account(validated_data)
        instance.referral_code = instance.generate_referral_code()
        instance.referral_reference = validated_data.get('referral_reference')
        instance.save()
        return instance

    def get_or_create_account(self, validated_data):
        acc, created = Account.objects.get_or_create(
            phone_no=validated_data['phone_no'])
        acc.pincode = validated_data.get('pincode')
        acc.pan_no = validated_data.get('pan_no')
        acc.save()
        return acc

    def get_user(self):
        return User.objects.get(username=self.validated_data['username'])


class AccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Account
        fields = ('phone_no', 'pincode', 'pan_no', 'alternate_no')


class UserSerializer(serializers.ModelSerializer):
    account = serializers.SerializerMethodField()

    def get_account(self, obj):
        return AccountSerializer(obj.account).data

    class Meta:
        model = User
        fields = (
            'id', 'username', 'user_type', 'email',
            'active', 'account', 'company'
        )
