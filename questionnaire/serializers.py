from rest_framework import serializers

from questionnaire.models import Question, Answer, Response
from utils import constants


class QuestionnSerializers(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()

    def get_answers(self, obj):
        return AnswerSerializer(obj.answer_set.all(), many=True).data

    class Meta:
        model = Question
        fields = ('category', 'question', 'answers')


class AnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Answer
        fields = ('id', 'question', 'answer')


class ResponseSerializer(serializers.Serializer):
    category_id = serializers.IntegerField(required=True)
    customer_segment_id = serializers.IntegerField(required=True)
    default = serializers.JSONField(required=True)
    answers = serializers.JSONField(required=True)

    def validate_category_id(self, value):
        from product.models import Category
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                constants.INVALID_CATEGORY_ID)
        return value

    def validate_customer_segment_id(self, value):
        from product.models import CustomerSegment
        if not CustomerSegment.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                constants.INVALID_CUSTOMER_SEGMENT)
        return value
