from rest_framework import serializers

from questionnaire.models import Question, Answer, Response


class QuestionnSerializers(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()

    def get_answer(self, obj):
        return AnswerSerializer(obj.answer_set.all(), many=True).data

    class Meta:
        model = Question
        fields = ('category', 'question', 'answers')


class AnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Answer
        fields = '__all__'


class ResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Response
        fields = '__all__'
