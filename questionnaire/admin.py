# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from questionnaire.models import Question, Answer, Response


class QuestionnaireAnswerInLine(admin.TabularInline):
    model = Answer
    max_num = 10


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'question', 'category', 'order')
    search_fields = ('category__name', 'category__id', 'id', 'title')
    raw_id_fields = ('category', )
    inlines = (QuestionnaireAnswerInLine, )


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'score')
    search_fields = ('question__id', 'id')
    raw_id_fields = ('question',)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'opportunity')
    search_fields = (
        'question__id', 'opportunity__lead__id',
        'opportunity__lead__user__account__phone_no')
    raw_id_fields = ('opportunity', 'question', 'answer')
