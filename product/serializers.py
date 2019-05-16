from rest_framework import serializers

from product.models import Category, Company
from content.serializers import FaqSerializer


class CategoryNameSerializers(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('id', 'name')


class CompanyNameSerializers(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = ('id', 'name')


class CategoryFaqSerializer(serializers.ModelSerializer):
    faqs = serializers.SerializerMethodField()

    def get_faqs(self, obj):
        return FaqSerializer(obj.faq_set.all(), many=True).data

    class Meta:
        model = Category
        fields = ('name', 'faqs')
