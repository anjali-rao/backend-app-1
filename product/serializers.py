from rest_framework import serializers

from product.models import Category, Company


class CategoryNameSerializers(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ('id', 'name')


class CompanyNameSerializers(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = ('id', 'name')
