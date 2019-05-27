from utils import constants as Constants
from rest_framework import serializers

from content.models import (
    Faq, ContactUs, NewsletterSubscriber, PromoBook,
    NetworkHospital, EnterprisePlaylist, Note)

from product.models import ProductVariant, Company


class FaqSerializer(serializers.ModelSerializer):
    category = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Faq
        fields = ('question', 'answer', 'category')


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
                Constants.INVALID_PHONE_NO_FORMAT)
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
    company_logo = serializers.ReadOnlyField(source='logo')
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
            'product', 'category', 'company_logo', 'sales_brochure',
            'claim_form')


class CompanyHelpLineSerializer(serializers.ModelSerializer):
    helplines = serializers.SerializerMethodField()

    def get_helplines(self, obj):
        return obj.helpline_set.values_list('number', flat=True)

    class Meta:
        model = Company
        fields = ('name', 'helplines')


class EnterprisePlaylistSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='playlist.name')
    playlist_id = serializers.SerializerMethodField()
    playlist_type = serializers.ReadOnlyField(source='playlist.playlist_type')

    def get_playlist_id(self, obj):
        return obj.playlist.url[
            obj.playlist.url.rfind('list'):].replace('list=', '')

    class Meta:
        model = EnterprisePlaylist
        fields = ('name', 'playlist_id', 'playlist_type')


class NotesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Note
        fields = ('title', 'text', 'read', 'id')
