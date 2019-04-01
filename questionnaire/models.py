# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.model import BaseModel, models
from utils import constants, get_choices


class Question(BaseModel):
    category = models.ForeignKey('product.Category')
    title = models.CharField(max_length=32)
    question_type = models.CharField(
        max_length=10, choices=get_choices(constants.QUESTION_COICES),
        default="single")
    question = models.TextField()
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class Answer(BaseModel):
    question = models.ForeignKey('questionnaire.Question')
    answer = models.CharField(max_length=128)
    score = models.IntegerField(default=0)

    def __str__(self):
        return self.answer


class Response(BaseModel):
    question = models.ForeignKey('questionnaire.Question')
    lead = models.ForeignKey('crm.Lead')
    answer = models.ForeignKey('questionnaire.Answer')

    def __str__(self):
        return '%s - %s | %s' % (
            self.question.title, self.answer.answer, self.lead.id
        )
