# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import get_choices, constants


#class TaskTemplate(BaseModel):
#    name = models.CharField(max_length=128)
#    category = models.CharField(max_length=62)
#    template = models.TextField()
#
#
#class Task(BaseModel):
#    """
#    Task to be run on every 30 min
#    """
#    task_type = models.CharField(
#        max_length=32, choices=get_choices(constants.TASK_CHOICES),
#        default='basic')
#    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
#    contact = models.ForeignKey(
#        'crm.Contact', on_delete=models.CASCADE, null=True, blank=True)
#    task_master = models.ForeignKey(
#        'activity.TaskTemplate', on_delete=models.CASCADE)
#    header = models.CharField(max_length=256)
#    description = models.TextField(null=True)
#    seen = models.BooleanField(default=False)
#    scheduled_time = models.DateTimeField(null=True)
#
#
#call,
#=================
#time
#person
#
#Meeting
#=================
#meeting,
#event,
#share,
#folloup,
#
#(0, 'Call'), (1, 'Meeting'), (2, 'Messages'), (3, 'Task'), (4, 'Event'))
