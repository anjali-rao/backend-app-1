from rest_framework import serializers

from content.models import Faq


class FaqSerializer(serializers.ModelSerializer):

    class Meta:
        model = Faq
        fields = '__all__'
