from utils import constants
from rest_framework import serializers

from content.models import (
    Faq, ContactUs, NewsletterSubscriber, PromoBook,
    NetworkHospital)


class FaqSerializer(serializers.ModelSerializer):

    class Meta:
        model = Faq
        fields = ('question', 'answer')


class ContactUsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactUs
        fields = ('full_name', 'phone_no', 'email', 'message')


class NewsLetterSerializer(serializers.ModelSerializer):

    class Meta:
        model = NewsletterSubscriber
        fields = ('email',)


class PromoBookSerializer(serializers.ModelSerializer):
    phone_no = serializers.CharField(required=True, max_length=10)

    def validate_phone_no(self, value):
        if value[0] in range(0, 4):
            raise serializers.ValidationError(
                constants.INVALID_PHONE_NO_FORMAT)
        return value

    class Meta:
        model = PromoBook
        fields = ('phone_no',)


class NetworkCoverageSerializer(serializers.ModelSerializer):
    company = serializers.ReadOnlyField(source='company.name')
    hospital_name = serializers.ReadOnlyField(source='name')
    address = serializers.ReadOnlyField(source='get_full_address')

    class Meta:
        model = NetworkHospital
        fields = ('company', 'hospital_name', 'address')
