from rest_framework import serializers

from content.models import NetworkHospital
from crm.models import Lead
from sales.models import Quote
from utils import constants


class CreateLeadSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=True)
    gender = serializers.CharField(required=True)
    pincode = serializers.CharField(required=True, max_length=6)

    def validate_category_id(self, value):
        from product.models import Category
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                constants.INVALID_CATEGORY_ID)
        return value

    def validate_gender(self, value):
        value = value.lower()
        if value not in constants.GENDER:
            raise serializers.ValidationError(
                constants.INVALID_GENDER_PROVIDED)
        return value

    class Meta:
        model = Lead
        fields = ('id', 'category_id', 'pincode', 'gender')

    @property
    def data(self):
        # TO DOS: Remove this when app is build
        super(CreateLeadSerializer, self).data
        self._data = dict(
            message='Lead created successfully',
            lead_id=self.instance.id
        )
        return self._data


class LeadSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    created = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_category(self, obj):
        return obj.category.name

    def get_full_name(self, obj):
        return obj.contact.get_full_name()

    def get_created(self, obj):
        return obj.created.strftime("%d/%m/%Y")

    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = Lead
        fields = ('id', 'category', 'full_name', 'status', 'created')


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


class QuoteDetailsSerializer(serializers.ModelSerializer):
    suminsured = serializers.SerializerMethodField()
    premium = serializers.SerializerMethodField()
    benefits = serializers.SerializerMethodField()
    coverage = serializers.SerializerMethodField()
    faq = serializers.SerializerMethodField()
    company_details = serializers.SerializerMethodField()

    def get_benefits(self, obj):
        benefits = []
        for f in obj.get_feature_details().exclude(
                short_description__in=['Not Covered', 'Not covered', '']):
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
            coverages_added.add(feature['feature_master__feature_type'])
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


class QuotesCompareSerializer(serializers.ModelSerializer):
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


class QuoteRecommendationSerializer(serializers.ModelSerializer):
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
        return obj.lead.adults

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'lead_id', 'sum_insured', 'premium',
            'tax_saving', 'wellness_rewards', 'health_checkups',
            'product', 'features'
        )
