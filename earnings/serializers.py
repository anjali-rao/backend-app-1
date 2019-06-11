from rest_framework import serializers

from earnings.models import Earning


class EarningSerializer(serializers.ModelSerializer):

    class Meta:
        model = Earning
        fields = ('text', 'amount', 'status', 'earning_type', 'payable_date')
