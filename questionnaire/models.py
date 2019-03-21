# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.model import BaseModel, models


class Question(BaseModel):
    category = models.ForeignKey('product.Category')
    question = models.TextField()

    [{"answer": "hello", "score": "10"}, {"answer": "no", "score": "9"}]


class Answer(BaseModel):
    question = models.ForeignKey('product.Question')
    answer = models.TextField()
    score = models.IntegerField(default=0)


class Response(BaseModel):
    question = models.ForeignKey('product.Question')
    lead = models.ForeignKey('crm.Lead')
    answer = models.CharField(max_length=64)
    score = models.IntegerField(default=0)
