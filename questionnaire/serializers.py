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
        if value not in constants.GENDER:
            raise serializers.ValidationError(
                constants.INVALID_GENDER_PROVIDED)
        return value

    def response(self):
        # TODOs get Quotes
        return {"no 1": 1212}


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
