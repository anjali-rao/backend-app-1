from rest_framework import serializers

from sales.models import Application, Member, Nominee, Quote
from crm.models import Contact
from users.models import Pincode, Address
from utils import constants, mixins

from django.db import transaction, IntegrityError


class CreateApplicationSerializer(serializers.ModelSerializer):
    quote_id = serializers.CharField(required=True)
    contact_name = serializers.CharField(required=True, write_only=True)
    contact_no = serializers.CharField(required=True, write_only=True)
    application_id = serializers.SerializerMethodField()
    application_reference_no = serializers.SerializerMethodField()

    def validate_quote_id(self, value):
        if not Quote.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                'Invalid Quote id provided.'
            )
        return value

    def create(self, validated_data):
        full_name = validated_data['contact_name'].split(' ')
        try:
            with transaction.atomic():
                instance = Application.objects.create(
                    quote_id=validated_data['quote_id'])
                lead = instance.quote.lead
                contact, created = Contact.objects.get_or_create(
                    phone_no=validated_data['contact_no'], parent=None)
                if created:
                    contact.update_fields(**dict(
                        user_id=lead.user.id, first_name=full_name[0]
                    ))
                lead.update_fields(**dict(
                    contact_id=contact.id, status='inprogress', stage='cart'
                ))
            return instance
        except IntegrityError:
            raise mixins.NotAcceptable(
                constants.APPLICATION_ALREAY_EXISTS)
        raise mixins.NotAcceptable(
            constants.FAILED_APPLICATION_CREATION)

    def get_application_id(self, obj):
        return obj.id

    def get_application_reference_no(self, obj):
        return obj.reference_no

    class Meta:
        model = Application
        fields = (
            'quote_id', 'application_id', 'application_reference_no',
            'contact_name', 'contact_no',)
        read_only_fields = ('reference_no',)


class GetProposalDetailsSerializer(serializers.ModelSerializer):
    document_type = serializers.SerializerMethodField()
    document_number = serializers.SerializerMethodField()
    contact_id = serializers.SerializerMethodField()
    pincode = serializers.SerializerMethodField()
    street = serializers.SerializerMethodField()
    flat_no = serializers.SerializerMethodField()

    def get_document_type(self, obj):
        if hasattr(obj, 'kycdocument'):
            return obj.kycdocument.document_type

    def get_document_number(self, obj):
        if hasattr(obj, 'kycdocument'):
            return obj.kycdocument.document_number

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

    def validate_pincode(self, value):
        if not Pincode.get_pincode(value):
            raise serializers.ValidationError(constants.INVALID_PINCODE)
        return value

    def save(self, **kwargs):
        validated_data = dict(
            list(self.validated_data.items()) +
            list(kwargs.items())
        )
        with transaction.atomic():
            contact, created = self.Meta.model.objects.get_or_create(
                phone_no=validated_data['phone_no']
            )
            if created:
                self.instance = contact
                self.instance.lead.update_fields(**dict(
                    contact_id=self.instance.id
                ))
            self.instance = super(
                UpdateContactDetailsSerializer, self).save(**kwargs)
            self.instance.update_fields(**dict(
                address_id=Address.objects.create(
                    pincode_id=Pincode.get_pincode(
                        validated_data['pincode']).id
                ).id,
                parent_id=(None if created else contact.id),
                is_client=True
            ))

    @property
    def data(self):
        # TO DOS: Remove this when app is build
        super(UpdateContactDetailsSerializer, self).data
        self._data = dict(
            message='Contact updated successfully'
        )
        return self._data

    class Meta:
        model = Contact
        fields = (
            'first_name', 'last_name', 'phone_no', 'dob', 'annual_income',
            'occupation', 'marital_status', 'email', 'pincode',
            'document_type', 'document_number', 'middle_name'
        )
        read_only_fields = (
            'document_type', 'document_number', 'pincode')


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
            self.Meta.model.objects.filter(
                relation=validated_data['relation'],
                application_id=validated_data['application_id'],
                ignore=None
            ).update(ignore=True)
            self.instance = None
        self.instance = super(CreateMemberSerializers, self).save(**kwargs)
        self.instance.ignore = False
        return self.instance.save()

    class Meta:
        model = Member
        fields = (
            'gender', 'first_name', 'middle_name', 'last_name', 'dob',
            'occupation', 'relation', 'height', 'weight', 'height_foot',
            'height_inches', 'id')
        read_only_fields = ('height_foot', 'height_inches')


class MemberSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.get_full_name()

    class Meta:
        model = Member
        fields = ('id', 'relation', 'full_name')


class GetApplicationMembersSerializer(serializers.ModelSerializer):
    height_foot = serializers.SerializerMethodField()
    height_inches = serializers.SerializerMethodField()

    def get_height_foot(self, obj):
        return obj.height_foot

    def get_height_inches(self, obj):
        return obj.height_inches

    class Meta:
        model = Member
        fields = (
            'application_id', 'gender', 'first_name', 'middle_name',
            'last_name', 'dob', 'occupation', 'relation', 'height_inches',
            'height_foot', 'weight'
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
        fields = ('first_name', 'middle_name', 'last_name', 'phone_no')
