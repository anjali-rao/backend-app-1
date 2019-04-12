from rest_framework import serializers
from rest_framework import exceptions, status

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
            raise exceptions.NotAcceptable(
                constants.APPLICATION_ALREAY_EXISTS,
                404)
        raise exceptions.NotAcceptable(
            constants.FAILED_APPLICATION_CREATION,
            status.HTTP_400_BAD_REQUEST)

    def get_application_id(self, obj):
        return obj.id

    def get_application_reference_no(self, obj):
        return obj.reference_no

    def get_contact_id(self, obj):
        if hasattr(self, 'contact'):
            return self.contact.id

    class Meta:
        model = Application
        fields = (
            'quote_id', 'application_id', 'application_reference_no',
            'contact_name', 'contact_no', 'contact_id')
        read_only_fields = ('reference_no',)


class GetProposalDetailsSerializer(serializers.ModelSerializer):
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
            'contact_id', 'first_name', 'last_name', 'phone_no', 'pincode',
            'annual_income', 'occupation', 'marital_status', 'email', 'dob',
            'document_type', 'document_number', 'document_type_choices',
            'occupation_choices'
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
        self.instance, created = self.Meta.model.objects.get_or_create(
            first_name=validated_data['first_name'],
            phone_no=validated_data['phone_no']
        )
        self.instance = super(
            UpdateContactDetailsSerializer, self).save(**kwargs)
        self.instance.address_id = Address.objects.create(
            pincode_id=Pincode.get_pincode(validated_data['pincode']).id
        ).id
        self.instance.save()
        if created:
            self.lead.contact_id = self.instance.id
            self.lead.save()

    class Meta:
        model = Contact
        fields = (
            'first_name', 'last_name', 'phone_no', 'dob', 'annual_income',
            'occupation', 'marital_status', 'email', 'pincode',
            'document_type', 'document_number'
        )
        read_only_fields = (
            'document_type', 'document_number', 'pincode')
