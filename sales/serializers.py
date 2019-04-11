from rest_framework import serializers

from sales.models import Application, Client
from rest_framework import exceptions
from crm.models import Contact
from users.models import Pincode, Address
from utils import constants

from django.db import transaction, IntegrityError


class CreateApplicationSerializer(serializers.ModelSerializer):
    quote_id = serializers.CharField(required=True)
    contact_name = serializers.CharField(required=True)
    phone_no = serializers.CharField(required=True)

    def create(self, validated_data):
        try:
            with transaction.atomic():
                instance = Application.objects.create(
                    quote_id=validated_data['quote_id'])
                if not Contact.objects.filter(
                        phone_no=validated_data['phone_no']).exists():
                    lead = instance.quote.lead
                    contact = Contact.objects.create(
                        user_id=lead.user.id, name=validated_data['name'],
                        phone_no=validated_data['phone_no']
                    )
                    lead.contact_id = contact.id
                    lead.status = 1  # In-Progress
                    lead.stage = 4  # In-Cart
                    lead.save()
                return instance
        except IntegrityError:
            raise exceptions.APIException(
                constants.FAILED_APPLICATION_CREATION)

    class Meta:
        models = Application
        fields = ('quote_id', 'reference_no')


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
        client, created = Client.objects.get_or_create(
            document_number=validated_data['kyc_document_number'])
        if created:
            # Update Client details via celery
            client.update_details(validated_data)
        return instance
