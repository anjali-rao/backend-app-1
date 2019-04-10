from rest_framework import serializers

from content.models import Faq, ContactUs


class FaqSerializer(serializers.ModelSerializer):

    class Meta:
        model = Faq
        fields = ('question', 'answer')


class ContactUsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactUs
        fields = ('full_name', 'phone_no', 'email', 'message')
