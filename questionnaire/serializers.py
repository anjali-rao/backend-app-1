from rest_framework import serializers

from questionnaire.models import Question, Answer, Response
from utils import constants as Constants


class QuestionnSerializers(serializers.ModelSerializer):
    question_id = serializers.ReadOnlyField(source='id')
    answers = serializers.SerializerMethodField()

    def get_answers(self, obj):
        return AnswerSerializer(
            obj.answer_set.filter(ignore=False), many=True).data

    class Meta:
        model = Question
        fields = (
            'question_id', 'title', 'question', 'question_type',
            'answers')


class AnswerSerializer(serializers.ModelSerializer):
    answer_id = serializers.ReadOnlyField(source='id')

    class Meta:
        model = Answer
        fields = ('answer_id', 'answer')


class ResponseSerializer(serializers.Serializer):
    opportunity_id = serializers.IntegerField(required=True)
    answers = serializers.JSONField(required=True)

    def validate_opportunity_id(self, value):
        from crm.models import Opportunity
        if not Opportunity.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                Constants.OPPORTUNITY_DOES_NOT_EXIST)
        return value

    def validate_customer_segment_id(self, value):
        from product.models import CustomerSegment
        if not CustomerSegment.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                Constants.INVALID_CUSTOMER_SEGMENT)
        return value

    def validate_answers(self, value):
        if not value or not isinstance(value, list):
            raise serializers.ValidationError(
                Constants.ANSWER_CANNOT_BE_LEFT_BLANK
            )
        serializer = QuestionnaireResponseSerializer(data=value, many=True)
        if not serializer.is_valid():
            error_list = []
            for errors in serializer.errors:
                if not errors:
                    continue
                error_list.extend([j for i in errors.values() for j in i])
            raise serializers.ValidationError(error_list)
        return value


class QuestionnaireResponseSerializer(serializers.ModelSerializer):
    answer_id = serializers.IntegerField(required=True)
    question_id = serializers.IntegerField(required=True)
    lead_id = serializers.IntegerField(required=False)

    def validate_answer_id(self, value):
        if not Answer.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                Constants.INVALID_ANSWER_ID % value)
        return value

    def validate_question_id(self, value):
        if not Question.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                Constants.INVALID_QUESTION_ID % value)
        return value

    class Meta:
        model = Response
        fields = ('question_id', 'answer_id', 'lead_id')
