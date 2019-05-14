# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import get_choices, constants
from product.models import Category

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Faq(BaseModel):
    question = models.CharField(max_length=264)
    answer = models.TextField()


class HelpLine(BaseModel):
    company = models.ForeignKey('product.Company', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    number = models.CharField(blank=True, max_length=32)


class HelpFile(BaseModel):
    title = models.CharField(max_length=62, null=True, blank=True)
    product_variant = models.ForeignKey(
        'product.ProductVariant', on_delete=models.CASCADE)
    file = models.FileField(upload_to=constants.HELP_FILES_PATH)
    file_type = models.CharField(
        choices=get_choices(constants.HELP_FILES_TYPE),
        default="all", max_length=32
    )

    def __str__(self):
        return '%s: %s %s' % (
            self.file_type.title().replace('_', ' '),
            self.product_variant.company_category.company.name,
            self.product_variant.company_category.category.name)

    class Meta:
        ordering = ('-created',)


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


class Playlist(BaseModel):
    name = models.CharField(max_length=32)
    url = models.URLField()
    playlist_type = models.CharField(
        max_length=32, choices=get_choices(constants.PLAYLIST_CHOICES))

    def __str__(self):
        return '%s | %s: %s' % (self.name, self.playlist_type, self.url)


class EnterprisePlaylist(BaseModel):
    limit = models.Q(app_label='users', model='enterprise') | \
        models.Q(app_label='users', model='subcriberenterprise')
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, limit_choices_to=limit)
    enterprise_id = models.PositiveIntegerField()
    enterprise = GenericForeignKey('content_type', 'enterprise_id')
    playlist = models.ForeignKey('content.Playlist', on_delete=models.CASCADE)

    def __str__(self):
        return '%s:%s' % (self.enterprise, self.playlist.name)


class Article(BaseModel):
    heading = models.CharField(max_length=256)
    tags = models.CharField(max_length=32, choices=get_choices(
        Category.objects.values_list('name', flat=True)))
    url = models.URLField()
    short_descripton = models.CharField(max_length=512)
    image = models.ImageField(null=True)


class Coverages(BaseModel):
    company_category = models.ForeignKey(
        'product.CompanyCategory', on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.TextField()
