# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.model import BaseModel, models
from utils import constants

# from django.contrib.postgres.fields import JSONField


class Quote(BaseModel):
    lead = models.ForeignKey('crm.Lead')
    status = models.CharField(
        max_length=16, choices=constants.QUOTE_STAUTS_CHOICES,
        default='pending')
    premium = models.ForeignKey('product.Premium', null=True, blank=True)

    def feature_score(self):
        return QuoteFeature.objects.filter(quote_id=self.id).aggregate(
            s=models.Sum('score'))['s']

    class Meta:
        unique_together = ('lead', 'premium',)


class QuoteFeature(BaseModel):
    quote = models.ForeignKey('sales.Quote', on_delete=models.CASCADE)
    feature = models.ForeignKey('product.feature', on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)


# class InsuranceApplication(BaseModel):
#     quote = models.OneToOneField(Quote)
#     status = models.CharField(max_length=127,choices=(('pending','Pending'),('accepted','Accepted'),('rejected','Rejected')),default='pending')
#     first_name = models.CharField(max_length=127, default="")
#     middle_name = models.CharField(max_length=127,null=True,blank=True)
#     last_name = models.CharField(max_length=127, default="")
#     date_of_birth = models.CharField(max_length=127, default="")
#     email = models.CharField(max_length=127, default="")
#     pan_number = models.CharField(max_length=127, default="")
#     contact_no = models.CharField(max_length=127, default="")
#     contact_no2 = models.CharField(max_length=127,null=True,blank=True)
#     address = models.TextField(null=True,blank=True)
#     appartment_no = models.CharField(max_length=127,null=True,blank=True)
#     city = models.CharField(max_length=127,null=True,blank=True)
#     zip_code = models.CharField(max_length=127,null=True,blank=True)
#     country = models.CharField(max_length=127,null=True,blank=True)
#     no_of_people_listed = models.IntegerField(null=True,blank=True)
# 
# 
# class HealthApplication(BaseModel):
#     quote = models.OneToOneField(Quote)
# 
# class Client(BaseModel):
#     pan = models.CharField(max_length=127)
#     first_name = models.CharField(max_length=127, default="")
#     middle_name = models.CharField(max_length=127,null=True,blank=True)
#     last_name = models.CharField(max_length=127, default="")
#     date_of_birth = models.CharField(max_length=127, default="")
#     email = models.CharField(max_length=127, default="")
#     contact_no = models.CharField(max_length=127, default="")
# 
# class Policy(BaseModel):
#     insurance_application = models.OneToOneField(InsuranceApplication)
#     contact = models.ForeignKey('crm.Contact')
#     client = models.ForeignKey(Client)
#     policy_data_json = JSONField()
