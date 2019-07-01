from rest_framework import serializers

from earnings.models import Earning


class EarningSerializer(serializers.ModelSerializer):
    status = serializers.ReadOnlyField(source='get_status_display')
    payable_date = serializers.SerializerMethodField()

    def get_payable_date(self, obj):
        date = obj.payable_date.strftime('%Y-%m-%dT%H:%m:%S.')
        date += obj.payable_date.strftime('%s')[:5] + '+05:30'
        return date

    class Meta:
        model = Earning
        fields = (
            'id', 'text', 'amount', 'status', 'earning_type', 'payable_date')
