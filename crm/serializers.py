from rest_framework import serializers

from content.models import NetworkHospital
from crm.models import Lead, Contact
from sales.models import Quote
from utils import constants


class CreateUpdateLeadSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=True)
    pincode = serializers.CharField(required=True, max_length=6)
    gender = serializers.CharField(required=False)
    family = serializers.JSONField(required=False)
    contact_id = serializers.IntegerField(required=False)
    stage = serializers.CharField(required=False)

    def validate_pincode(self, value):
        from users.models import Pincode
        if not Pincode.get_pincode(value):
            raise serializers.ValidationError(constants.INVALID_PINCODE)
        return value

    def validate_category_id(self, value):
        from product.models import Category
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                constants.INVALID_CATEGORY_ID)
        return value

    def validate_gender(self, value):
        if value.lower() not in constants.GENDER:
            raise serializers.ValidationError(
                constants.INVALID_GENDER_PROVIDED)
        return value

    def validate_family(self, value):
        if not value:
            raise serializers.ValidationError(
                constants.INVALID_FAMILY_DETAILS)
        for member, age in value.items():
            if not isinstance(age, int) and not age.isdigit():
                raise serializers.ValidationError(
                    constants.INVALID_FAMILY_DETAILS)
        return value

    def contact_id(self, value):
        contacts = Contact.objects.filter(id=value)
        if not contacts.exists():
            raise serializers.ValidationError(constants.INVALID_CONTACT_ID)
        return value

    def validate_stage(self, value):
        if value not in [s for s, S in constants.LEAD_STAGE_CHOICES]:
            raise serializers.ValidationError(constants.INVALID_LEAD_STAGE)
        return value

    class Meta:
        model = Lead
        fields = (
            'id', 'category_id', 'pincode', 'family', 'gender',
            'contact_id', 'stage')

    @property
    def data(self):
        # TO DOS: Remove this when app is build
        super(CreateUpdateLeadSerializer, self).data
        self._data = dict(
            message='Lead operation successfully processed.',
            lead_id=self.instance.id
        )
        return self._data


class LeadSerializer(serializers.ModelSerializer):
    category = serializers.ReadOnlyField(source='category.name')
    full_name = serializers.ReadOnlyField(source='contact.get_full_name')
    stage = serializers.ReadOnlyField(source='get_stage_display')
    bookmark = serializers.ReadOnlyField(source='bookmark')

    class Meta:
        model = Lead
        fields = (
            'id', 'category', 'full_name', 'stage', 'bookmark', 'created')


class QuoteSerializer(serializers.ModelSerializer):
    quote_id = serializers.ReadOnlyField(source='id')
    status = serializers.ReadOnlyField(source='get_status_display')
    sum_insured = serializers.ReadOnlyField(source='premium.sum_insured')
    premium = serializers.ReadOnlyField(source='premium.amount')
    product = serializers.ReadOnlyField(
        source='premium.product_variant.get_product_details')

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'lead_id', 'sum_insured', 'premium',
            'product', 'recommendation_score', 'status'
        )


class QuoteDetailsSerializer(serializers.ModelSerializer):
    suminsured = serializers.ReadOnlyField(source='premium.sum_insured')
    premium = serializers.ReadOnlyField(source='premium.amount')
    benefits = serializers.SerializerMethodField()
    coverage = serializers.SerializerMethodField()
    faq = serializers.ReadOnlyField(source='get_faq')
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

    def get_company_details(self, obj):
        details = obj.premium.product_variant.get_product_details()
        details.update(obj.premium.product_variant.get_basic_details())
        return details

    class Meta:
        model = Quote
        fields = (
            'id', 'suminsured', 'premium', 'coverage', 'benefits', 'faq',
            'company_details')


class QuotesCompareSerializer(serializers.ModelSerializer):
    quote_id = serializers.ReadOnlyField(source='id')
    suminsured = serializers.ReadOnlyField(source='premium.sum_insured')
    premium = serializers.ReadOnlyField(source='premium.amount')
    product = serializers.ReadOnlyField(
        source='premium.product_variant.get_product_details')
    features = serializers.SerializerMethodField()
    network_coverage = serializers.SerializerMethodField()

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
        company = obj.premium.product_variant.company_category.company.name
        return [dict(
            name='hospitals',
            value=NetworkHospital.objects.select_related(
                'pincode', 'company').filter(
                    pincode__pincode=obj.lead.pincode,
                    company__name=company).count()
        )]

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'suminsured', 'premium', 'product',
            'features', 'network_coverage'
        )


class QuoteRecommendationSerializer(serializers.ModelSerializer):
    quote_id = serializers.ReadOnlyField(source='id')
    sum_insured = serializers.ReadOnlyField(source='premium.sum_insured')
    premium = serializers.ReadOnlyField(source='premium.amount')
    tax_saving = serializers.ReadOnlyField(source='lead.tax_saving')
    wellness_rewards = serializers.ReadOnlyField(
        source='lead.wellness_rewards')
    health_checkups = serializers.ReadOnlyField(source='lead.adults')
    product = serializers.ReadOnlyField(
        source='premium.product_variant.get_product_details')
    features = serializers.SerializerMethodField()

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

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'lead_id', 'sum_insured', 'premium',
            'tax_saving', 'wellness_rewards', 'health_checkups',
            'product', 'features'
        )


class LeadDetailSerializer(serializers.ModelSerializer):
    lead_id = serializers.ReadOnlyField(source='id')
    stage = serializers.ReadOnlyField(source='get_stage_display')
    phone_no = serializers.ReadOnlyField(source='contact.phone_no')
    address = serializers.ReadOnlyField(source='contact.address.full_address')
    quotes = serializers.SerializerMethodField()

    def get_quotes(self, obj):
        return QuoteSerializer(
            obj.quote_set.filter(ignore=False), many=True).data

    class Meta:
        model = Lead
        fields = ('lead_id', 'phone_no', 'address', 'stage', 'quotes')
