from rest_framework import serializers

from sales.models import (
    Application, Member, Nominee, Quote, HealthInsurance,
    TravelInsurance, ExistingPolicies
)
from crm.models import Contact, KYCDocument
from users.models import Pincode, Address
from utils import constants, mixins

from django.db import transaction, IntegrityError


class CreateApplicationSerializer(serializers.ModelSerializer):
    application_id = serializers.ReadOnlyField(source='id', read_only=True)
    quote_id = serializers.CharField(required=True)
    contact_name = serializers.CharField(required=True, write_only=True)
    contact_no = serializers.CharField(required=True, write_only=True)

    def validate_quote_id(self, value):
        if not Quote.objects.filter(id=value).exists():
            raise serializers.ValidationError(constants.INVALID_QUOTE_ID)
        return value

    def create(self, validated_data):
        full_name = validated_data['contact_name'].split(' ')
        try:
            with transaction.atomic():
                quote = Quote.objects.get(id=validated_data['quote_id'])
                instance = Application.objects.create(
                    quote_id=validated_data['quote_id'],
                    premium=quote.premium.amount,
                    suminsured=quote.premium.sum_insured)
                lead = quote.lead
                contact, created = Contact.objects.get_or_create(
                    phone_no=validated_data['contact_no'])
                if created:
                    contact.update_fields(**dict(
                        user_id=lead.user.id, first_name=full_name[0]))
                lead.update_fields(**dict(
                    contact_id=contact.id, status='inprogress', stage='cart'))
            return instance
        except IntegrityError as e:
            raise mixins.NotAcceptable(
                constants.APPLICATION_ALREAY_EXISTS)
        raise mixins.NotAcceptable(
            constants.FAILED_APPLICATION_CREATION)

    class Meta:
        model = Application
        fields = (
            'quote_id', 'application_id', 'contact_name', 'contact_no',)
        read_only_fields = ('reference_no',)


class GetProposalDetailsSerializer(serializers.ModelSerializer):
    document_type = serializers.SerializerMethodField()
    document_number = serializers.SerializerMethodField()
    contact_id = serializers.SerializerMethodField()
    pincode = serializers.SerializerMethodField()
    street = serializers.SerializerMethodField()
    flat_no = serializers.SerializerMethodField()

    def get_document_type(self, obj):
        kyc_docs = obj.kycdocument_set.all()
        if kyc_docs.exists():
            return kyc_docs.latest('modified').document_type
        return ''

    def get_document_number(self, obj):
        kyc_docs = obj.kycdocument_set.all()
        if kyc_docs.exists():
            return kyc_docs.latest('modified').document_number
        return ''

    def get_contact_id(self, obj):
        return obj.id

    def get_pincode(self, obj):
        if hasattr(obj, 'address') and hasattr(obj.address, 'pincode'):
            return obj.address.pincode.pincode
        return ''

    def get_street(self, obj):
        if hasattr(obj, 'address') and hasattr(obj.address, 'pincode'):
            return obj.address.street
        return ''

    def get_flat_no(self, obj):
        if hasattr(obj, 'address') and hasattr(obj.address, 'pincode'):
            return obj.address.flat_no
        return ''

    class Meta:
        model = Contact
        fields = (
            'contact_id', 'first_name', 'middle_name', 'last_name', 'phone_no',
            'pincode', 'annual_income', 'occupation', 'marital_status', 'dob',
            'email', 'document_type', 'document_number', 'street', 'flat_no'
        )


class UpdateContactDetailsSerializer(serializers.ModelSerializer):
    document_type = serializers.CharField(required=True)
    document_number = serializers.CharField(required=True)
    pincode = serializers.CharField(required=True)
    street = serializers.CharField(required=True)
    flat_no = serializers.CharField(required=True)

    def validate_pincode(self, value):
        if not Pincode.get_pincode(value):
            raise serializers.ValidationError(constants.INVALID_PINCODE)
        return value

    def save(self, **kwargs):
        validated_data = dict(
            list(self.validated_data.items()) +
            list(kwargs.items()))
        app = Application.objects.get(id=validated_data['application_id'])
        with transaction.atomic():
            update_fields = dict(
                address_id=Address.objects.create(
                    pincode_id=Pincode.get_pincode(
                        validated_data['pincode']).id,
                    flat_no=validated_data['flat_no'],
                    street=validated_data['street']
                ).id
            )
            members = Member.objects.filter(
                application_id=app.id, relation='self')
            if self.instance.phone_no != validated_data['phone_no']:
                instances = self.Meta.model.objects.filter(
                    phone_no=validated_data['phone_no'])
                if instances.exists():
                    self.instance = instances.latest('modified')
                else:
                    self.instance = None
                    update_fields['user_id'] = app.quote.lead.user.id
            elif members.exists():
                member = members.get()
                member.update_fields(**dict(
                    first_name=validated_data['first_name'],
                    last_name=validated_data['last_name'],
                    occupation=validated_data['occupation'],
                    dob=validated_data['dob']))
            self.instance = super(
                UpdateContactDetailsSerializer, self).save(**kwargs)
            kycdocument, created = KYCDocument.objects.get_or_create(
                document_type=validated_data['document_type'],
                contact_id=self.instance.id)
            kycdocument.document_number = validated_data['document_number']
            kycdocument.save()
            self.instance.update_fields(**update_fields)
            app.update_fields(**dict(
                status='pending', client_id=self.instance.id))

    def create(self, valid_data):
        """
        We have a bit of extra checking around this in order to provide
        descriptive messages when something goes wrong, but this method is
        essentially just:
            return ExampleModel.objects.create(**validated_data)
        If there are many to many fields present on the instance then they
        cannot be set until the model is instantiated, in which case the
        implementation is like so:
            example_relationship = validated_data.pop('example_relationship')
            instance = ExampleModel.objects.create(**validated_data)
            instance.example_relationship = example_relationship
            return instance
        The default implementation also does not handle nested relationships.
        If you want to support writable nested relationships you'll need
        to write an explicit `.create()` method.
        """
        from rest_framework.serializers import raise_errors_on_nested_writes
        import traceback
        from rest_framework.utils import model_meta
        raise_errors_on_nested_writes('create', self, valid_data)

        ModelClass = self.Meta.model

        # Remove many-to-many relationships from validated_data.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in valid_data):
                many_to_many[field_name] = valid_data.pop(field_name)
        validated_data = dict()
        for field_name in valid_data.keys():
            if field_name in constants.CONTACT_CREATION_FIELDS:
                validated_data[field_name] = valid_data[field_name]
        try:
            instance = ModelClass._default_manager.create(**validated_data)
        except TypeError:
            tb = traceback.format_exc()
            msg = (
                'Got a `TypeError` when calling `%s.%s.create()`. '
                'This may be because you have a writable field on the '
                'serializer class that is not a valid argument to '
                '`%s.%s.create()`. You may need to make the field '
                'read-only, or override the %s.create() method to handle '
                'this correctly.\nOriginal exception was:\n %s' %
                (
                    ModelClass.__name__, ModelClass._default_manager.name,
                    ModelClass.__name__, ModelClass._default_manager.name,
                    self.__class__.__name__,
                    tb
                )
            )
            raise TypeError(msg)

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                field = getattr(instance, field_name)
                field.set(value)

        return instance

    @property
    def data(self):
        self._data = dict(
            message='Contact updated successfully'
        )
        return self._data

    class Meta:
        model = Contact
        fields = (
            'first_name', 'last_name', 'phone_no', 'dob', 'annual_income',
            'occupation', 'marital_status', 'email', 'pincode',
            'document_type', 'document_number', 'middle_name',
            'flat_no', 'street'
        )
        read_only_fields = (
            'document_type', 'document_number', 'pincode', 'flat_no', 'street')


class CreateMemberSerializers(serializers.ModelSerializer):
    dob = serializers.DateField(format='yyyy-mm-dd', required=True)
    height_foot = serializers.FloatField(required=True)
    height_inches = serializers.FloatField(required=True)

    def validate_height_foot(self, value):
        return value * 30.48

    def validate_height_inches(self, value):
        return value * 2.54

    def save(self, **kwargs):
        self.validated_data['height'] = self.validated_data[
            'height_foot'] + self.validated_data['height_inches']
        del self.validated_data['height_inches']
        del self.validated_data['height_foot']
        validated_data = dict(
            list(self.validated_data.items()) + list(kwargs.items())
        )
        self.instance = self.Meta.model.objects.filter(
            application_id=validated_data['application_id'],
            relation=validated_data['relation']
        ).first()
        if validated_data['relation'] in ['son', 'daughter']:
            self.instance = None
        self.instance = super(CreateMemberSerializers, self).save(**kwargs)
        self.instance.ignore = False
        return self.instance.save()

    class Meta:
        model = Member
        fields = (
            'first_name', 'last_name', 'dob', 'relation',
            'height', 'weight', 'height_foot', 'height_inches', 'id')
        read_only_fields = ('height_foot', 'height_inches')


class MemberSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(source='get_full_name')

    class Meta:
        model = Member
        fields = ('id', 'relation', 'full_name')


class GetApplicationMembersSerializer(serializers.ModelSerializer):

    class Meta:
        model = Member
        fields = (
            'application_id', 'gender', 'first_name', 'last_name', 'dob',
            'occupation', 'relation', 'height_inches', 'height_foot', 'weight'
        )


class CreateNomineeSerializer(serializers.ModelSerializer):

    @property
    def data(self):
        # TO DOS: Remove this when app is build
        super(CreateNomineeSerializer, self).data
        self._data = dict(
            message='Nominee added successfully.'
        )
        return self._data

    class Meta:
        model = Nominee
        fields = ('first_name', 'last_name', 'relation', 'phone_no')


class NomineeSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(source='get_full_name')

    class Meta:
        model = Nominee
        fields = ('full_name', 'phone_no', 'relation')


class HealthInsuranceSerializer(serializers.ModelSerializer):

    class Meta:
        model = HealthInsurance
        fields = (
            "gastrointestinal_disease", "neuronal_diseases", "ent_diseases",
            "respiratory_diseases", "cardiovascular_disease", "blood_diseases",
            "alcohol_consumption", "tobacco_consumption", "previous_claim",
            "proposal_terms", "oncology_disease", "cigarette_consumption")

    @property
    def data(self):
        # TO DOS: Remove this when app is build
        super(HealthInsuranceSerializer, self).data
        self._data = dict(
            message='Contact updated successfully'
        )
        return self._data


class TravalInsuranceSerializer(serializers.ModelSerializer):

    class Meta:
        model = TravelInsurance
        fields = '__all__'


class TermsSerializer(serializers.ModelSerializer):
    terms_and_conditions = serializers.BooleanField(required=True)

    class Meta:
        model = Application
        fields = ('terms_and_conditions',)

    @property
    def data(self):
        # TO DOS: Remove this when app is build
        super(TermsSerializer, self).data
        self._data = dict(
            message='Application updated successfully.',
            status=self.instance.get_status_display(),
            reference_no=self.instance.reference_no
        )
        return self._data


INSURANCE_SERIALIZER_MAPPING = {
    'healthinsurance': HealthInsuranceSerializer,
    'travelinsurance': TravalInsuranceSerializer
}


def get_insurance_serializer(application_type):
    return INSURANCE_SERIALIZER_MAPPING.get(application_type)


class ExistingPolicySerializer(serializers.ModelSerializer):

    class Meta:
        model = ExistingPolicies
        fields = ('insurer', 'suminsured', 'deductible')

    @property
    def data(self):
        # TO DOS: Remove this when app is build
        self._data = dict(
            message='Existing policies added successfully.'
        )
        return self._data


class GetInsuranceFieldsSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)
    field_name = serializers.CharField(required=True)
    field_requirements = serializers.JSONField(required=True)


class ApplicationSummarySerializer(serializers.ModelSerializer):
    proposer_details = serializers.SerializerMethodField()
    insured_members = serializers.SerializerMethodField()
    nominee_details = serializers.SerializerMethodField()
    existing_policies = serializers.SerializerMethodField()

    def get_proposer_details(self, obj):
        return GetProposalDetailsSerializer(self.instance.client).data

    def get_insured_members(self, obj):
        members = sorted(
            self.instance.active_members,
            key=lambda member: constants.MEMBER_ORDER.get(
                member.relation, 0))
        return GetApplicationMembersSerializer(
            members, many=True).data

    def get_nominee_details(self, obj):
        return NomineeSerializer(self.instance.nominee_set.first()).data

    def get_existing_policies(self, obj):
        return ExistingPolicySerializer(
            self.instance.existingpolicies_set.all(), many=True).data

    class Meta:
        model = Application
        fields = (
            'proposer_details', 'insured_members', 'nominee_details',
            'existing_policies'
        )


class SalesApplicationSerializer(serializers.ModelSerializer):
    proposer_name = serializers.SerializerMethodField()
    product_name = serializers.ReadOnlyField(
        source='quote.premium.product_variant.product_short_name')
    section = serializers.SerializerMethodField()
    earning = serializers.SerializerMethodField()
    last_updated = serializers.DateTimeField(source='modified')
    logo = serializers.ReadOnlyField(
        source='quote.premium.product_variant.logo')

    def get_earning(self, obj):
        return ''

    def get_section(self, obj):
        return self.context.get('section', '-')

    def get_proposer_name(self, obj):
        instance = obj.client or obj.quote.lead.contact
        return instance.get_full_name()

    class Meta:
        model = Application
        fields = (
            'id', 'reference_no', 'premium', 'suminsured', 'earning',
            'last_updated', 'logo', 'section', 'product_name', 'proposer_name',
            'stage'
        )


class ClientSerializer(serializers.ModelSerializer):
    company_logo = serializers.ReadOnlyField(
        source='quote.premium.product_variant.logo')
    product_name = serializers.ReadOnlyField(
        source='quote.premium.product_variant.product_short_name')
    full_name = serializers.SerializerMethodField()
    status = serializers.ReadOnlyField(source='get_status_display')

    def get_full_name(self, obj):
        instance = obj.client or obj.quote.lead.contact
        return instance.get_full_name()

    class Meta:
        model = Application
        fields = (
            'id', 'product_name', 'full_name', 'created', 'premium',
            'status', 'company_logo')
