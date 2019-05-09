# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import get_choices, constants

from product.models import Category


class Faq(BaseModel):
    question = models.CharField(max_length=264)
    answer = models.TextField()


class HelpFile(BaseModel):
    title = models.CharField(blank=True, max_length=512)
    file = models.FileField(upload_to=constants.HELP_FILES_PATH)
    file_type = models.CharField(
        choices=get_choices(constants.HELP_FILES_TYPE),
        default="ALL", max_length=128
    )
    category = models.CharField(
        choices=get_choices(
            Category.objects.values_list('name', flat=True), 'ALL'
        ), default="ALL", max_length=512)


class ContactUs(BaseModel):
    full_name = models.CharField(max_length=512)
    phone_no = models.CharField(max_length=10)
    email = models.EmailField(max_length=50)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{} - {}".format(self.phone_no, self.full_name)


class NetworkHospital(BaseModel):
    name = models.CharField(blank=True, max_length=100)
    city = models.CharField(max_length=64)
    address = models.TextField()
    contact_number = models.CharField(blank=True, max_length=100)


class NewsletterSubscriber(BaseModel):
    email = models.EmailField()
    unsubscribe = models.BooleanField(default=False)


class PhoneNumber(BaseModel):
    phone_no = models.CharField(max_length=10, )
