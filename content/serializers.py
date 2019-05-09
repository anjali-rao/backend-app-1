from utils import constants
from rest_framework import serializers

from content.models import Faq, ContactUs, NewsletterSubscriber, PhoneNumber


class FaqSerializer(serializers.ModelSerializer):

    class Meta:
        model = Faq
        fields = ('question', 'answer')


class ContactUsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactUs
        fields = ('full_name', 'phone_no', 'email', 'message')


class NewsLetterSerializer(serializers.ModelSerializer):

    class Meta:
        model = NewsletterSubscriber
        fields = ('email',)


class SubmitPhoneNumberSerializer(serializers.ModelSerializer):
    phone_no = serializers.CharField(required=True)

    def validate_phone_no(self, value):
        import pdb; pdb.set_trace()
        if value[0] in range(0, 4):
            raise serializers.ValidationError(
                constants.INVALID_PHONE_NO_FORMAT)
        return value

    class Meta:
        model = PhoneNumber
        fields = ('phone_no',)