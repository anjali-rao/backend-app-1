from rest_framework import serializers
from rest_framework import exceptions

from sales.models import Application
from crm.models import Contact
from users.models import Pincode, Address
from utils import constants

from django.db import transaction, IntegrityError


class CreateApplicationSerializer(serializers.ModelSerializer):
    quote_id = serializers.CharField(required=True)
    contact_name = serializers.CharField(required=True, write_only=True)
    contact_no = serializers.CharField(required=True, write_only=True)
    application_id = serializers.SerializerMethodField()
    application_reference_no = serializers.SerializerMethodField()
    contact_id = serializers.SerializerMethodField()

    def create(self, validated_data):
        full_name = validated_data['contact_name'].split(' ')
        try:
            with transaction.atomic():
                instance = Application.objects.create(
                    quote_id=validated_data['quote_id'])
                lead = instance.quote.lead
                contacts = Contact.objects.filter(
                    phone_no=validated_data['contact_no'])
                if not contacts.exists():
                    contact = Contact.objects.create(
                        user_id=lead.user.id, first_name=full_name[0],
                        phone_no=validated_data['contact_no'],
                        last_name=(
                            full_name[1] if len(full_name) == 2 else None)
                    )
                else:
                    contact = contacts.get()
                lead.contact_id = contact.id
                lead.status = 'inprogress'
                lead.stage = 'cart'
                lead.save()
                self.contact = contact
            return instance
        except IntegrityError:
            raise exceptions.APIException(
                constants.FAILED_APPLICATION_CREATION)

    def get_application_id(self, obj):
        return obj.id

    def get_application_reference_no(self, obj):
        return obj.reference_no

    def get_contact_id(self, obj):
        if hasattr(self, 'contact_id'):
            return self.contact.id

    class Meta:
        model = Application
        fields = (
            'quote_id', 'application_id', 'application_reference_no',
            'contact_name', 'contact_no', 'contact_id')
        read_only_fields = ('reference_no',)


class GetContactDetailsSerializer(serializers.ModelSerializer):
    document_type = serializers.SerializerMethodField()
    document_number = serializers.SerializerMethodField()
    document_type_choices = serializers.SerializerMethodField()
    occupation_choices = serializers.SerializerMethodField()
    contact_id = serializers.SerializerMethodField()

    def get_document_type(self, obj):
        try:
            return obj.kycdocument.document_type
        except Exception:
            pass

    def get_document_number(self, obj):
        try:
            return obj.kycdocument.document_number
        except Exception:
            pass

    def get_document_type_choices(self, obj):
        return constants.DOC_TYPES

    def get_occupation_choices(self, obj):
        return constants.OCCUPATION_CHOICES

    def get_contact_id(self, obj):
        return obj.id

    class Meta:
        model = Contact
        fields = (
            'contact_id', 'first_name', 'last_name', 'phone_no', 'dob',
            'annual_income', 'occupation', 'marital_status', 'email',
            'document_type', 'document_number', 'document_type_choices',
            'occupation_choices', 'pincode'
        )


class UpdateContactDetailsSerializer(serializers.ModelSerializer):
    application_id = serializers.CharField(required=True)
    document_type = serializers.CharField(required=True)
    document_number = serializers.CharField(required=True)
    contact_id = serializers.CharField(required=True)

    def validate_pincode(self, value):
        if not Pincode.get_pincode(value):
            raise serializers.ValidationError(constants.INVALID_PINCODE)
        return value

    def validate_contact_id(self, value):
        contacts = self.Meta.model.objects.filter(id=value)
        if not contacts.exists():
            raise serializers.ValidationError(constants.INVALID_CONTACT_ID)
        self.contact = contacts.get()
        return value

    def save(self, **kwargs):
        contact_creation_required = False
        validated_data = dict(
            list(self.validated_data.items()) +
            list(kwargs.items())
        )
        contact = self.Meta.model.objects.get(id=validated_data['contact_id'])
        if contact.first_name != validated_data['first_name']:
            contact_creation_required = True
        elif contact.phone_no != validated_data['phone_no']:
            contact_creation_required = True
        if not contact_creation_required:
            self.instance = contact
        instance = super(UpdateContactDetailsSerializer, self).save(**kwargs)
        if contact_creation_required:
            self.lead.contacts.add(instance.id)
            self.lead.save()

    def get_contact_id(self, obj):
        return obj.id

    class Meta:
        model = Contact
        fields = (
            'first_name', 'last_name', 'phone_no', 'dob', 'annual_income',
            'occupation', 'marital_status', 'email', 'document_type',
            'document_number', 'pincode', 'contact_id'
        )
        read_only_fields = (
            'document_type', 'document_number', 'application_id')


class UpdateApplicationSerializer(serializers.ModelSerializer):
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
        return instance
