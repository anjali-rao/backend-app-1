# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import constants, get_choices


class Question(BaseModel):
    category = models.ForeignKey('product.Category', on_delete=models.CASCADE)
    title = models.CharField(max_length=32)
    question_type = models.CharField(
        max_length=10, choices=get_choices(constants.QUESTION_COICES),
        default="single")
    question = models.TextField()
    order = models.IntegerField(default=0)
    ignore = models.BooleanField(default=False)

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return self.title


class Answer(BaseModel):
    question = models.ForeignKey(
        'questionnaire.Question', on_delete=models.CASCADE)
    answer = models.CharField(max_length=128)
    order = models.IntegerField(default=0)
    ignore = models.BooleanField(default=False)
    score = models.IntegerField(default=0)

    class Meta:
        ordering = ('order',)

    def __str__(self):
        return self.answer


class Response(BaseModel):
    question = models.ForeignKey(
        'questionnaire.Question', on_delete=models.CASCADE)
    lead = models.ForeignKey(
        'crm.Lead', on_delete=models.CASCADE)
    answer = models.ForeignKey(
        'questionnaire.Answer', on_delete=models.CASCADE)

    def __str__(self):
        return '%s - %s | %s' % (
            self.question.title, self.answer.answer, self.lead.id
        )
