from rest_framework import serializers

from questionnaire.models import Question, Answer, Response
from utils import constants


class QuestionnSerializers(serializers.ModelSerializer):
    question_id = serializers.SerializerMethodField()
    answers = serializers.SerializerMethodField()

    def get_question_id(self, obj):
        return obj.id

    def get_answers(self, obj):
        return AnswerSerializer(obj.answer_set.all(), many=True).data

    class Meta:
        model = Question
        fields = (
            'question_id', 'title', 'question', 'question_type',
            'answers')


class AnswerSerializer(serializers.ModelSerializer):
    answer_id = serializers.SerializerMethodField()

    def get_answer_id(self, obj):
        return obj.id

    class Meta:
        model = Answer
        fields = ('answer_id', 'answer')


class ResponseSerializer(serializers.Serializer):
    category_id = serializers.IntegerField(required=True)
    gender = serializers.CharField(required=True)
    pincode = serializers.CharField(required=True, max_length=6)
    family = serializers.JSONField(required=True)
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

    def validate_answers(self, value):
        serializer = QuestionnaireResponseSerializer(data=value, many=True)
        serializer.is_valid(raise_exception=True)
        return value

    def validate_gender(self, value):
        if value.lower() not in constants.GENDER:
            raise serializers.ValidationError(
                constants.INVALID_GENDER_PROVIDED)
        return value


class QuestionnaireResponseSerializer(serializers.ModelSerializer):
    answer_id = serializers.CharField(required=True)
    question_id = serializers.CharField(required=True)
    lead_id = serializers.CharField(required=False)

    def validate_answer_id(self, value):
        if not Answer.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                constants.INVALID_ANSWER_ID)
        return value

    def validate_question_id(self, value):
        if not Question.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                constants.INVALID_QUESTION_ID)
        return value

    class Meta:
        model = Response
        fields = ('question_id', 'answer_id', 'lead_id')