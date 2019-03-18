from rest_framework import serializers

from  product.models import Company, CompanyDetails


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company
        fields = '__all__'
