from rest_framework import serializers

from sales.models import Quote, Application, Client
from users.models import Pincode, Address
from utils import constants

from content.models import NetworkHospital


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
        for f in obj.premium.product_variant.feature_set.exclude(
            short_description__in=[
                'Data unavailable', '', 'Not covered', 'Not Covered']
        ).order_by('-rating').values(
                'feature_master__name', 'short_description')[:5]:
            features.append('%s: %s' % (
                f['feature_master__name'], f['short_description']))
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


class QuotesDetailsSerializer(serializers.ModelSerializer):
    suminsured = serializers.SerializerMethodField()
    premium = serializers.SerializerMethodField()
    benefits = serializers.SerializerMethodField()
    coverage = serializers.SerializerMethodField()
    faq = serializers.SerializerMethodField()
    company_details = serializers.SerializerMethodField()

    def get_benefits(self, obj):
        benefits = []
        for f in obj.get_feature_details().exclude(
                short_description__in=['Not Covered', 'Not covered', ''])[:5]:
            benefits.append({
                'name': f['feature_master__name'].title(),
                'description': f['short_description']
            })
        return benefits

    def get_coverage(self, obj):
        coverages_added = set()
        coverages = list()
        features = obj.premium.product_variant.feature_set.values(
            'feature_master__feature_type',
            'feature_master__name')
        for feature in features:
            try:
                find_coverage = next(
                    coverage for coverage in coverages if coverage['name'] == feature[ # noqa
                        'feature_master__feature_type'])
                find_coverage['value'].append(
                    feature['feature_master__name'])
            except StopIteration:
                coverages.append({
                    'name': feature['feature_master__feature_type'],
                    'value': [feature['feature_master__name']]
                })
            coverages_added.add(feature['feature_master__name'])
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
        features = list()
        for f in obj.get_feature_details():
            features.append({
                'name': f['feature_master__name'].title(),
                'description': f['feature_master__long_description'],
                'short_text': (
                    f['short_description'] or 'Not Covered').title()
            })
        return features

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
