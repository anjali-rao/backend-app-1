# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from utils.model import BaseModel, models
from utils import constants


class Contact(BaseModel):
    user = models.ForeignKey('users.User')
    name = models.CharField(max_length=32)
    phone = models.CharField(max_length=10)
    email = models.EmailField(max_length=64, null=True, blank=True)
    pincode = models.CharField(max_length=6, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    occupation = models.IntegerField(
        choices=constants.OCCUPATION_CHOICES,
        default=constants.OCCUPATION_DEFAULT_CHOICE)
    is_married = models.BooleanField(default=False)
    # education_status = models.IntegerField(choices=((0,''),(1,'')),null=True,blank=True)
    is_parent_dependent = models.BooleanField(default=False)
    other_dependents = models.IntegerField(default=0)
    income = models.FloatField(default=0.0)
    no_of_kids = models.IntegerField(default=0)
    status = models.IntegerField(
        choices=((0, 'Fresh'), (1, 'Other')), default=0)
    medical_history = models.BooleanField(default=False)
    is_default = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = ('user', 'phone',)


class Lead(BaseModel):
    contact = models.ForeignKey(Contact)
    category = models.ForeignKey('product.Category')
    amount = models.FloatField(default=0.0)
    final_score = models.FloatField(default=0.0)
    status = models.IntegerField(
        choices=constants.LEAD_STATUS_CHOICES, default=0)
    stage = models.IntegerField(
        choices=constants.LEAD_STAGE_CHOICES)
    product_id = models.IntegerField(null=True, blank=True)
    # notes = models.ManyToManyField(Note)
    campaign = models.ForeignKey('users.Campaign')

    def __unicode__(self):
        return "%s - %s" % (
            self.contact.name, self.category.name)

    def calculate_final_score(self):
        from product.models import QuestionAnswer
        final_score = sum(list(
            QuestionAnswer.objects.filter(
                lead_id=self.id).values_list('score', flat=True))
        )
        self.final_score = final_score
        self.save()

    def next_activity_date_time(self):
        # if Activity.objects.filter(lead__id = self.id):
        #     activity = Activity.objects.filter(lead__id = self.id,due_date__gte=datetime.today().date()).order_by('due_date','due_time')[0]
        #     return activity.due_time.strftime("%H:%M %p")+", "+activity.due_date.strftime("%d %b")
        return "No Activity Found"