from utils import constants
from rest_framework import serializers

from content.models import (
    Faq, ContactUs, NewsletterSubscriber, PromoBook,
    NetworkHospital, HelpLine)

from product.models import ProductVariant, Company


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


class ProductVariantHelpFileSerializer(serializers.ModelSerializer):
    company = serializers.ReadOnlyField(source='company_category.company.name')
    product = serializers.ReadOnlyField(source='name')
    category = serializers.ReadOnlyField(
        source='company_category.category.name')
    sales_brochure = serializers.SerializerMethodField()
    claim_form = serializers.SerializerMethodField()

    def get_sales_brochure(self, obj):
        helpfile = obj.helpfile_set.filter(file_type='sales_brochure').first()
        if helpfile:
            return helpfile.file.url
        return '-'

    def get_claim_form(self, obj):
        helpfile = obj.helpfile_set.filter(file_type='claim_form').first()
        if helpfile:
            return helpfile.file.url
        return '-'

    class Meta:
        model = ProductVariant
        fields = (
            'product', 'category', 'company', 'sales_brochure', 'claim_form')


class CompanyHelpLineSerializer(serializers.ModelSerializer):
    helplines = serializers.SerializerMethodField()

    def get_helplines(self, obj):
        return obj.helpline_set.values_list('number', flat=True)

    class Meta:
        model = Company
        fields = ('name', 'helplines')
