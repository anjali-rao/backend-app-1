from rest_framework import serializers

from sales.models import Quote, QuoteFeature


class QuoteSerializers(serializers.ModelSerializer):
    premium = serializers.SerializerMethodField()
    product = serializers.SerializerMethodField()
    customer_segment_feature_score = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    def get_premium(self, obj):
        return obj.premium.get_details()

    def get_product(self, obj):
        return obj.premium.product_variant.get_product_details()

    def get_customer_segment_feature_score(self, obj):
        return obj.feature_score()

    def get_features(self, obj):
        return QuoteFeature(obj.quotefeature_set.all(), many=True).data

    class Meta:
        model = Quote
        fields = (
            'id', 'status', 'lead_id', 'premium', 'product',
            'customer_segment_feature_score', 'features'
        )


class QuoteFeature(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    feature_master_id = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.feature.feature_master.id

    def get_description(self, obj):
        return obj.feature.feature_master.description

    def get_feature_master_id(self, obj):
        return obj.feature.feature_master.id

    class Meta:
        model = QuoteFeature
        fields = ('id', 'name', 'score', 'description', 'feature_master_id')
