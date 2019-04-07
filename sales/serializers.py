from rest_framework import serializers

from sales.models import Quote, QuoteFeature, Application, Client
from users.models import Pincode, Address
from utils import constants

from content.models import NetworkHospital

from django.db.models import F


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
        return obj.premium.sum_insured

    def get_premium(self, obj):
        return obj.premium.amount

    def get_features(self, obj):
        features = list()
        for f in obj.quotefeature_set.annotate(
            feature_master_name=F('feature__feature_master__name'),
            feature_value=F('feature__short_description')
        ).values('feature_master_name', 'feature_value').order_by(
                '-feature__rating'):
            features.append('%s: %s' % (
                f['feature_master_name'], f['feature_value']))
        return features

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
        return obj.premium.sum_insured

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
        return obj.feature.short_description

    class Meta:
        model = QuoteFeature
        fields = ('id', 'name', 'score', 'description')


class QuotesDetailsSerializer(serializers.ModelSerializer):
    suminsured = serializers.SerializerMethodField()
    premium = serializers.SerializerMethodField()
    benefits = serializers.SerializerMethodField()
    coverage = serializers.SerializerMethodField()
    faq = serializers.SerializerMethodField()
    company_details = serializers.SerializerMethodField()

    def get_benefits(self, obj):
        return QuoteFeatureSerializer(
            obj.quotefeature_set.all(), many=True).data

    def get_coverage(self, obj):
        features = obj.quotefeature_set.values(
            'feature__feature_master__feature_type',
            'feature__feature_master__name')
        coverages_added = set()
        coverages = []
        for feature in features:
            try:
                find_coverage = next(
                    coverage for coverage in coverages if coverage['name'] == feature[ # noqa
                        'feature__feature_master__feature_type'])
                find_coverage['value'].append(
                    feature['feature__feature_master__name'])
            except StopIteration:
                coverages.append({
                    'name': feature['feature__feature_master__feature_type'],
                    'value': [feature['feature__feature_master__name']]
                })
            coverages_added.add(feature['feature__feature_master__name'])
        for pending in set(constants.FEATURE_TYPES) - set(coverages_added):
            coverages.append({'name': pending, 'value': None})
        return coverages

    def get_faq(self, obj):
        return obj.get_faq()

    def get_company_details(self, obj):
        details = obj.premium.product_variant.get_product_details()
        details.update(obj.premium.product_variant.get_basic_details())
        return details

    def get_suminsured(self, obj):
        return obj.premium.sum_insured

    def get_premium(self, obj):
        return obj.premium.amount

    class Meta:
        model = Quote
        fields = (
            'id', 'suminsured', 'premium', 'coverage', 'benefits', 'faq',
            'company_details')


class CompareSerializer(serializers.ModelSerializer):
    quote_id = serializers.SerializerMethodField()
    suminsured = serializers.SerializerMethodField()
    premium = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    network_coverage = serializers.SerializerMethodField()

    def get_quote_id(self, obj):
        return obj.id

    def get_suminsured(self, obj):
        return obj.premium.sum_insured

    def get_premium(self, obj):
        return obj.premium.amount

    def get_product(self, obj):
        return obj.premium.product_variant.get_product_details()

    def get_features(self, obj):
        return obj.get_feature_details()

    def get_network_coverage(self, obj):
        return [
            {
                'name': 'hospitals',
                'value': NetworkHospital.objects.filter(
                    city=obj.lead.city).count()
            }
        ]

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'suminsured', 'premium', 'product',
            'features', 'network_coverage'
        )


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
