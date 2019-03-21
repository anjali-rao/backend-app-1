# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.model import BaseModel, models


class Question(BaseModel):
    category = models.ForeignKey('product.Category')
    question = models.TextField()


class Answer(BaseModel):
    question = models.ForeignKey('questionnaire.Question')
    answer = models.CharField(max_length=128)
    score = models.IntegerField(default=0)


class Response(BaseModel):
    question = models.ForeignKey('questionnaire.Question')
    lead = models.ForeignKey('crm.Lead')
    answer = models.ForeignKey('questionnaire.Answer')
