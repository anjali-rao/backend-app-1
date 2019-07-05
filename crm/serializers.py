from rest_framework import serializers

from content.models import NetworkHospital
from content.serializers import NotesSerializer
from crm.models import Lead, Contact, Opportunity
from sales.models import Quote
from utils import constants as Constants, mixins, parse_phone_no

from django.db import transaction


class LeadCRUDSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=False)
    pincode = serializers.CharField(required=False, max_length=6)
    gender = serializers.CharField(required=False)
    family = serializers.JSONField(required=False)
    contact_name = serializers.CharField(required=False)
    contact_phone_no = serializers.CharField(required=False)

    def validate_pincode(self, value):
        from users.models import Pincode
        if not Pincode.get_pincode(value):
            raise serializers.ValidationError(Constants.INVALID_PINCODE)
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

    def get_contact(self, validated_data, **kwargs):
        name = validated_data['contact_name'].lower().split(' ')
        valid, validated_data['contact_phone_no'] = parse_phone_no(
            validated_data['contact_phone_no'])
        first_name = name[0]
        middle_name = name[1] if len(name) == 3 else ''
        last_name = name[2] if len(name) > 2 else (
            name[1] if len(name) == 2 else '')
        instance, created = Contact.objects.get_or_create(
            phone_no=validated_data['contact_phone_no'],
            first_name=first_name, middle_name=middle_name,
            last_name=last_name)
        if created:
            instance.user_id = validated_data['user_id']
            instance.save()
        return instance

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

    def save(self, **kwargs):
        validated_data = dict(
            list(self.validated_data.items()) + list(kwargs.items()))
        with transaction.atomic():
            if 'contact_name' in validated_data and (
                    'contact_phone_no' in validated_data):
                kwargs['contact_id'] = self.get_contact(
                    validated_data, **kwargs).id
            self.instance = super(LeadCRUDSerializer, self).save(**kwargs)

    class Meta:
        model = Lead
        fields = (
            'category_id', 'pincode', 'gender', 'family', 'contact_name',
            'contact_phone_no')
        abstract = True


class CreateLeadSerializer(LeadCRUDSerializer):
    opportunity_id = None

    def validate_category_id(self, value):
        from product.models import Category
        categories = Category.objects.filter(id=value)
        if not categories.exists() or not categories.get().is_active:
            raise serializers.ValidationError(Constants.INVALID_CATEGORY_ID)
        return value

    def create(self, validated_data):
        fields = dict.fromkeys(Constants.GENERIC_LEAD_FIELDS, None)
        for field in fields.keys():
            fields[field] = validated_data.get(field, None)
            if field in ['bookmark', 'ignore']:
                fields[field] = False
        if 'contact_id' in validated_data and self.Meta.model.objects.filter(
                contact_id=fields['contact_id']).exists():
            raise mixins.APIException(Constants.DUPLICATE_LEAD)
        self.instance = super(self.__class__, self).create(fields)
        if 'category_id' in validated_data:
            self.opportunity_id = self.instance.create_opportunity(
                validated_data).id
        return self.instance

    @property
    def data(self):
        self._data = dict(
            message='Lead created successfully.',
            lead_id=self.instance.id,
            opportunity_id=self.opportunity_id)
        return self._data

    class Meta:
        model = Lead
        fields = (
            'category_id', 'pincode', 'gender', 'family', 'contact_name',
            'contact_phone_no')


class UpdateLeadSerializer(LeadCRUDSerializer):
    opportunity_id = serializers.IntegerField(required=False)
    opportunity = None

    def validate_opportunity_id(self, value):
        opportunitys = Opportunity.objects.filter(id=value)
        if not opportunitys.exists():
            raise serializers.ValidationError(
                Constants.OPPORTUNITY_DOES_NOT_EXIST)
        self.opportunity = opportunitys.get()
        if self.opportunity.lead_id != self.instance.id:
            raise serializers.ValidationError(
                Constants.OPPORTUNITY_DOES_NOT_EXIST)
        return value

    def update(self, instance, validated_data):
        if instance.contact_id and 'contact_id' in validated_data:
            raise mixins.APIException(Constants.CONTACT_FORBIDDEN)
        fields = dict.fromkeys(Constants.GENERIC_LEAD_FIELDS, None)
        for field in fields.keys():
            fields[field] = validated_data.get(
                field, getattr(self.instance, field))
        self.instance = super(self.__class__, self).update(instance, fields)
        if 'opportunity_id' in validated_data:
            self.opportunity.update_category_opportunity(validated_data)
        elif 'category_id' in validated_data:
            self.opportunity = self.instance.create_opportunity(validated_data)
        return self.instance

    @property
    def data(self):
        self._data = dict(
            message='Lead updated successfully.',
            lead_id=self.instance.id,
            opportunity_id=self.opportunity.id)
        return self._data

    class Meta:
        model = Lead
        fields = (
            'pincode', 'gender', 'family', 'contact_name',
            'contact_phone_no', 'opportunity_id', 'category_id')


class LeadSerializer(serializers.ModelSerializer):
    category = serializers.ReadOnlyField(source='category.name')
    full_name = serializers.ReadOnlyField(source='contact.get_full_name')
    stage = serializers.ReadOnlyField(source='get_stage_display')

    class Meta:
        model = Lead
        fields = (
            'id', 'category', 'full_name', 'stage', 'bookmark', 'created')


class ClientSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(
        source='contact.get_full_name')

    class Meta:
        model = Lead
        fields = ('id', 'full_name', 'created')


class QuoteSerializer(serializers.ModelSerializer):
    quote_id = serializers.ReadOnlyField(source='id')
    category = serializers.ReadOnlyField(source='opportunity.category.name')
    category_logo = serializers.ImageField(source='opportunity.category.logo')
    lead_id = serializers.ReadOnlyField(source='opportunity.lead_id')
    status = serializers.ReadOnlyField(source='get_status_display')
    sum_insured = serializers.ReadOnlyField(source='premium.sum_insured')
    premium = serializers.ReadOnlyField(source='premium.amount')
    product = serializers.ReadOnlyField(
        source='premium.product_variant.get_product_details')
    sale_stage = serializers.SerializerMethodField()
    application_id = serializers.SerializerMethodField()

    def get_sale_stage(self, obj):
        if hasattr(obj, 'application'):
            return obj.application.stage
        return 'product_details'

    def get_application_id(self, obj):
        if hasattr(obj, 'application'):
            return obj.application.id
        return 0

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'opportunity_id', 'sum_insured', 'premium',
            'product', 'recommendation_score', 'status', 'sale_stage',
            'application_id', 'lead_id', 'category', 'category_logo')


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
                'description': f['short_description']})
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
                    pincode__pincode=obj.opportunity.lead.pincode,
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
    lead_id = serializers.ReadOnlyField(source='opportunity.lead_id')
    sum_insured = serializers.ReadOnlyField(source='premium.sum_insured')
    premium = serializers.ReadOnlyField(source='premium.amount')
    tax_saving = serializers.ReadOnlyField(
        source='opportunity.category_opportunity.tax_saving')
    wellness_rewards = serializers.SerializerMethodField()
    health_checkups = serializers.ReadOnlyField(
        source='opportunity.category_opportunity.adults')
    product = serializers.ReadOnlyField(
        source='premium.product_variant.get_product_details')
    features = serializers.SerializerMethodField()

    def get_features(self, obj):
        features = list()
        feature_set = list()
        if obj.premium.product_variant.parent:
            feature_set = list(self.get_sorted_features(
                obj.premium.product_variant.parent))
        feature_set.extend(self.get_sorted_features(
            obj.premium.product_variant))
        for f in feature_set[:5]:
            features.append('%s: %s' % (
                f.feature_master.name, f.short_description))
        return features

    def get_wellness_rewards(self, obj):
        if obj.get_feature_details().filter(
                feature_master__name='Wellness Factors'):
            return obj.opportunity.category_opportunity.wellness_reward
        return 0.0

    def get_sorted_features(self, variant):
        return sorted(
            variant.feature_set.exclude(
                short_description__in=[
                    'Data unavailable', '', 'Not covered', 'Not Covered']
            ), key=lambda feature: Constants.RECOMMENDATION_FEATURE_ORDER.get(
                feature.feature_master.name, 999))

    class Meta:
        model = Quote
        fields = (
            'quote_id', 'opportunity_id', 'sum_insured', 'premium',
            'tax_saving', 'wellness_rewards', 'health_checkups',
            'product', 'features', 'lead_id', 'recommendation_score')


class LeadDetailSerializer(serializers.ModelSerializer):
    lead_id = serializers.ReadOnlyField(source='id')
    full_name = serializers.ReadOnlyField(
        source='contact.get_full_name', default='')
    logo = serializers.FileField(source='category.logo', default='')
    stage = serializers.ReadOnlyField(source='get_stage_display')
    phone_no = serializers.ReadOnlyField(source='contact.phone_no')
    address = serializers.ReadOnlyField(source='contact.address.full_address')
    quotes = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()

    def get_quotes(self, obj):
        return QuoteSerializer(
            obj.get_quotes().filter(
                ignore=False, status='accepted'), many=True).data

    def get_notes(self, obj):
        return NotesSerializer(obj.note_set.all(), many=True).data

    class Meta:
        model = Lead
        fields = (
            'lead_id', 'phone_no', 'logo', 'address', 'stage', 'quotes',
            'created', 'notes', 'full_name')


class SharedQuoteDetailsSerializer(serializers.ModelSerializer):
    suminsured = serializers.ReadOnlyField(source='premium.sum_insured')
    premium = serializers.ReadOnlyField(source='premium.amount')
    benefits = serializers.SerializerMethodField()
    company_details = serializers.SerializerMethodField()

    def get_benefits(self, obj):
        benefits = []
        for f in obj.get_feature_details().exclude(
                short_description__in=['Not Covered', 'Not covered', '']):
            benefits.append({
                'name': f['feature_master__name'].title(),
                'description': f['short_description']})
        return benefits

    def get_company_details(self, obj):
        details = obj.premium.product_variant.get_product_details()
        details.update(obj.premium.product_variant.get_basic_details())
        return details

    class Meta:
        model = Quote
        fields = (
            'suminsured', 'premium', 'benefits', 'company_details',
            'tax_saving', 'wellness_reward', 'health_checkup',
            'effective_premium')
