# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.model import BaseModel, models
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
    category = models.CharField(max_length=100)


class ContactUs(BaseModel):
    title = models.CharField(max_length=512)
    description = models.TextField()
    value = models.CharField(max_length=100)
    value_type = models.CharField(
        choices=get_choices(constants.CONTACT_CHANNELS),
        default="phone",
        max_length=255)


class NetworkHospital(BaseModel):
    name = models.CharField(blank=True, max_length=100)
    city = models.CharField(max_length=64)
    address = models.TextField()
    contact_number = models.CharField(blank=True, max_length=100)
