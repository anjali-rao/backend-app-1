# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import get_choices, constants


class Faq(BaseModel):
    question = models.CharField(max_length=264)
    answer = models.TextField()


class HelpFile(BaseModel):
    company_category = models.ForeignKey(
        'product.CompanyCategory', on_delete=models.CASCADE)
    file = models.FileField(upload_to=constants.HELP_FILES_PATH)
    file_type = models.CharField(
        choices=get_choices(constants.HELP_FILES_TYPE),
        default="all", max_length=32
    )

    def __str__(self):
        return '%s: %s %s' % (
            self.file_type.title().replace('_', ' '),
            self.company_category.company.name,
            self.company_category.category.name)


class ContactUs(BaseModel):
    full_name = models.CharField(max_length=512)
    phone_no = models.CharField(max_length=10)
    email = models.EmailField(max_length=50)
    message = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{} - {}".format(self.phone_no, self.full_name)


class NetworkHospital(BaseModel):
    name = models.CharField(blank=True, max_length=256, db_index=True)
    company = models.ForeignKey(
        'product.Company', null=True, on_delete=models.CASCADE, blank=True)
    pincode = models.ForeignKey(
        'users.Pincode', on_delete=models.CASCADE, blank=True)
    address = models.TextField()
    contact_number = models.CharField(
        blank=True, max_length=100, db_index=True)

    def get_full_address(self):
        return '%s, %s, %s (%s)' % (
            self.address, self.pincode.city, self.pincode.state,
            self.pincode.pincode)


class NewsletterSubscriber(BaseModel):
    email = models.EmailField()
    unsubscribe = models.BooleanField(default=False)


class PromoBook(BaseModel):
    phone_no = models.CharField(max_length=10)

    def save(self, *args, **kwargs):
        from users.tasks import send_sms
        send_sms(self.phone_no, constants.PROMO_MESSAGE % self.phone_no)
        super(PromoBook, self).save(*args, **kwargs)
