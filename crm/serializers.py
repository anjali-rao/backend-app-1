from rest_framework import serializers

from content.models import NetworkHospital
from crm.models import Lead, Contact
from sales.models import Quote
from utils import constants as Constants

from django.db import transaction, IntegrityError


class CreateUpdateLeadSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=True)
    pincode = serializers.CharField(required=True, max_length=6)
    gender = serializers.CharField(required=False)
    family = serializers.JSONField(required=False)
    stage = serializers.CharField(required=False)
    contact_name = serializers.CharField(required=False)
    contact_phone_no = serializers.CharField(required=False)

    def validate_pincode(self, value):
        from users.models import Pincode
        if not Pincode.get_pincode(value):
            raise serializers.ValidationError(Constants.INVALID_PINCODE)
        return value

    def validate_contact_name(self, value):
        if 'contact_phone_no' not in self.initial_data:
            raise serializers.ValidationError(
                Constants.CONTACT_DETAILS_REQUIRED)
        return value

    def validate_contact_phone_no(self, value):
        if 'contact_name' not in self.initial_data:
            raise serializers.ValidationError(
                Constants.CONTACT_DETAILS_REQUIRED)
        return value

    def validate_gender(self, value):
        if value.lower() not in Constants.GENDER:
            raise serializers.ValidationError(
                Constants.INVALID_GENDER_PROVIDED)
        return value

    def validate_family(self, value):
        if not value:
            raise serializers.ValidationError(
                Constants.INVALID_FAMILY_DETAILS)
        for member, age in value.items():
            if not isinstance(age, int) and not age.isdigit():
                raise serializers.ValidationError(
                    Constants.INVALID_FAMILY_DETAILS)
        return value

    def validate_stage(self, value):
        if value not in [s for s, S in Constants.LEAD_STAGE_CHOICES]:
            raise serializers.ValidationError(Constants.INVALID_LEAD_STAGE)
        return value

    def create(self, validated_data):
        fields = dict.fromkeys(Constants.GENERIC_LEAD_FIELDS, None)
        for field in fields.keys():
            fields[field] = validated_data.get(field, None)
            if field == 'bookmark':
                fields[field] = False
        self.instance = super(self.__class__, self).create(fields)
        self.update_category_lead(validated_data)
        return self.instance

    def update_category_lead(self, validated_data):
        self.instance.refresh_from_db()
        category_lead = getattr(self.instance, self.instance.category_name)
        fields = dict.fromkeys(Constants.CATEGORY_LEAD_FIELDS_MAPPER[
            self.instance.category_name], None)
        for field in fields.keys():
            fields[field] = validated_data.get(field, None)
        category_lead.update_fields(**fields)
        return category_lead

    def update(self, validated_data):
        fields = dict.fromkeys(Constants.GENERIC_LEAD_FIELDS, None)
        for field in fields.keys():
            fields[field] = validated_data.get(
                field, getattr(self.instance, field))
        self.instance = super(self.__class__, self).update(fields)
        self.update_category_lead(validated_data)
        return self.instance

    def save(self, **kwargs):
        validated_data = dict(
            list(self.validated_data.items()) +
            list(kwargs.items()))
        with transaction.atomic():
            if 'contact_name' in validated_data and (
                    'contact_phone_no' in validated_data):
                self.create_or_update_contact()
            self.instance = super(
                CreateUpdateLeadSerializer, self).save(**kwargs)

    def create_or_update_contact(self, validated_data):
        contact, created = Contact.objects.get_or_create(
            user_id=self.request.user.id,
            phone_no=validated_data['contact_phone_no'])
        name = validated_data['contact_name'].split(' ')
        contact.first_name = name[0]
        contact.middle_name = name[1] if len(name) == 3 else ''
        contact.last_name = name[2] if len(name) == 3 else name[1]
        contact.save()

    class Meta:
        model = Lead
        fields = (
            'id', 'category_id', 'pincode', 'family', 'gender',
            'contact_phone_no', 'stage', 'contact_name')

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
        for pending in set(Constants.FEATURE_TYPES) - set(coverages_added):
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
    tax_saving = serializers.ReadOnlyField(
        source='lead.category_lead.tax_saving')
    wellness_rewards = serializers.ReadOnlyField(
        source='lead.category_lead.wellness_reward')
    health_checkups = serializers.ReadOnlyField(
        source='lead.category_lead.adults')
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
        fields = (
            'lead_id', 'phone_no', 'address', 'stage', 'quotes',
            'created')
