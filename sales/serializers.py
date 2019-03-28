from rest_framework import serializers

from sales.models import Quote, QuoteFeature, Application, Client
from users.models import Pincode, Address
from utils import constants

from content.serializers import FaqSerializer, Faq


class RecommendationSerializer(serializers.ModelSerializer):
    quote_id = serializers.SerializerMethodField()
    sum_insured = serializers.SerializerMethodField()
    premium = serializers.SerializerMethodField()
    tax_saving = serializers.SerializerMethodField()
    wellness_rewards = serializers.SerializerMethodField()
    health_checkups = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    def get_quote_id(self, obj):
        return obj.id

    def get_sum_insured(self, obj):
        return obj.premium.sum_insured.number

    def get_premium(self, obj):
        return round(obj.premium.amount, 2)

    def get_features(self, obj):
        return obj.quotefeature_set.values_list(
            'feature__feature_master__name', flat=True)

    def get_product(self, obj):
        return obj.premium.product_variant.get_product_details()

    def get_tax_saving(self, obj):
        return obj.lead.tax_saving

    def get_wellness_rewards(self, obj):
        return obj.lead.wellness_rewards

    def get_health_checkups(self, obj):
        return obj.lead.health_checkups

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'lead_id', 'sum_insured', 'premium',
            'tax_saving', 'wellness_rewards', 'health_checkups',
            'product', 'features'
        )


class QuoteSerializer(serializers.ModelSerializer):
    quote_id = serializers.SerializerMethodField()
    sum_insured = serializers.SerializerMethodField()
    premium = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    recommendation_score = serializers.SerializerMethodField()

    def get_quote_id(self, obj):
        return obj.id

    def get_sum_insured(self, obj):
        return obj.premium.sum_insured.number

    def get_premium(self, obj):
        return obj.premium.amount

    def get_product(self, obj):
        return obj.premium.product_variant.get_product_details()

    def get_recommendation_score(seld, obj):
        return obj.recommendation_score

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'lead_id', 'sum_insured', 'premium',
            'product', 'recommendation_score'
        )


class QuoteFeatureSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.feature.feature_master.name

    def get_description(self, obj):
        return obj.feature.feature_master.description

    class Meta:
        model = QuoteFeature
        fields = ('id', 'name', 'score', 'description')


class QuotesDetailsSerializer(serializers.ModelSerializer):
    benifits = serializers.SerializerMethodField()
    coverage = serializers.SerializerMethodField()
    faq = serializers.SerializerMethodField()
    company_details = serializers.SerializerMethodField()

    def get_benifits(self, obj):
        return QuoteFeatureSerializer(
            obj.quotefeature_set.all(), many=True).data

    def get_coverage(self, obj):
        coverage = dict.fromkeys(constants.FEATURE_TYPES)
        features = obj.quotefeature_set.values(
            'feature__feature_master__feature_type',
            'feature__feature_master__name')
        for feature in features:
            if not coverage[feature['feature__feature_master__feature_type']]:
                coverage[feature[
                    'feature__feature_master__feature_type']] = set()
            coverage[feature['feature__feature_master__feature_type']].add(
                feature['feature__feature_master__name'])
        return coverage

    def get_faq(self, obj):
        return FaqSerializer(Faq.objects.all(), many=True).data

    def get_company_details(self, obj):
        details = obj.premium.product_variant.get_product_details()
        details.update(obj.premium.product_variant.get_basic_details())
        return details

    class Meta:
        model = Quote
        fields = ('id', 'coverage', 'benifits', 'faq', 'company_details')


class CompareSerializer(serializers.ModelSerializer):
    quote_id = serializers.SerializerMethodField()
    sum_insured = serializers.SerializerMethodField()
    premium = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    coverage = serializers.SerializerMethodField()

    def get_quote_id(self, obj):
        return obj.id

    def get_sum_insured(self, obj):
        return obj.premium.sum_insured.number

    def get_premium(self, obj):
        return obj.premium.amount

    def get_product(self, obj):
        return obj.premium.product_variant.get_product_details()

    def get_features(self, obj):
        return QuoteFeatureSerializer(
            obj.quotefeature_set.all(), many=True).data

    def network_coverage(self, obj):
        pass

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'sum_insured', 'premium', 'product',
            'features', 'coverage'
        )


class CompareFeaturesSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuoteFeature
        fields = ('')


class CreateApplicationSerializer(serializers.ModelSerializer):
    quote_id = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    middle_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    dob = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    contact_no = serializers.CharField(required=True)
    alternate_no = serializers.CharField(required=True)
    street = serializers.CharField(required=True)
    pincode = serializers.CharField(required=True)
    kyc_document_type = serializers.CharField(max_length=64, required=True)
    kyc_document_number = serializers.CharField(max_length=64, required=True)

    def validate_pincode(self, value):
        if not Pincode.get_pincode(value):
            raise serializers.ValidationError(constants.INVALID_PINCODE)
        return value

    class Meta:
        model = Application
        fields = (
            'people_listed', 'pincode', 'first_name', 'middle_name', 'dob',
            'last_name', 'email', 'contact_no', 'alternate_no', 'street',
            'pincode', 'kyc_document_type', 'kyc_document_number', 'quote_id'
        )

    def create(self, validated_data):
        data = {
            'quote_id': validated_data['quote_id'],
            'address_id': Address.objects.create(
                pincode_id=Pincode.get_pincode(validated_data['pincode']).id,
                street=validated_data['street']
            ).id,
            'people_listed': validated_data['people_listed']
        }
        instance = Application.objects.create(**data)
        client, created = Client.objects.get_or_create(
            document_number=validated_data['kyc_document_number'])
        if created:
            # Update Client details via celery
            client.update_details(validated_data)
        return instance
