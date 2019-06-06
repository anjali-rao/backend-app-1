from django.contrib.postgres.fields import JSONField
from django.utils.functional import cached_property

from utils.models import BaseModel, models
from payment.models import ApplicationRequestLog
from aggregator import Constant
from aggregator.wallnut import evaluateClassName

import requests
import re


class Application(BaseModel):
    _host = 'https://wallnut.in/%s'
    reference_app = models.OneToOneField(
        'sales.application', on_delete=models.PROTECT)
    section = models.CharField(max_length=16)
    company_name = models.CharField(max_length=64, null=True)
    suminsured = models.CharField(max_length=16)
    premium = models.FloatField(default=0.0)
    insurance_type = models.CharField(max_length=16)
    quote_id = models.CharField(max_length=128, null=True)
    customer_code = models.CharField(max_length=64, null=True, blank=True)
    product_code = models.CharField(max_length=64, null=True, blank=True)
    producer_code = models.CharField(max_length=64, null=True, blank=True)
    city_code = models.CharField(max_length=16, null=True)
    state_code = models.CharField(max_length=16, null=True)
    dealstage = models.CharField(max_length=32, null=True)
    user_id = models.CharField(max_length=16, null=True)
    proposal_id = models.CharField(max_length=32, null=True)
    proposal_id2 = models.CharField(max_length=32, null=True)
    customer_id = models.CharField(max_length=32, null=True)
    city = models.CharField(max_length=16, null=True)
    state = models.CharField(max_length=16, null=True)
    pincode = models.CharField(max_length=16, null=True)
    payment_ready = models.BooleanField(default=False)
    regenerate_payment_link = models.BooleanField(default=True)
    raw_quote = JSONField(default=dict)
    insurer_product = None

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        if self.company_name:
            self.insurer_product = evaluateClassName(
                self.company_name, self.insurance_type)(self)

    def save(self, *args, **kwargs):
        try:
            self.__class__.objects.get(pk=self.id)
        except self.__class__.DoesNotExist:
            self.handle_creation()
        super(self.__class__, self).save(*args, **kwargs)

    def get_payment_link(self):
        return self.insurer_product.get_payment_link()

    def send_payment_link(self):
        from users.tasks import send_sms
        message = Constant.PAYMENT_MESSAGE % (
            self.proposer.get_full_name(),
            self.reference_app.reference_no, self.premium,
            self.reference_app.quote.premium.product_variant.__str__(),
            self.get_payment_link())
        send_sms(self.reference_app.client.phone_no, message)

    def handle_creation(self):
        self.section = Constant.SECTION.get(
            self.reference_app.application_type)
        self.suminsured = int(self.reference_app.suminsured)
        self.premium = self.reference_app.premium
        self.pincode = self.reference_app.quote.lead.pincode
        self.dealstage = 'productshortlisted'
        self.get_state_city()
        self.generate_quote_id()
        self.get_quote_data()

    def get_state_city(self):
        url = 'https://wallnut.in/health/proposal_aditya_birla/get_state_city?Pincode=%s' % ( # noqa
            self.reference_app.quote.lead.pincode)
        request_log = ApplicationRequestLog.objects.create(
            application_id=self.reference_app.id, url=url, request_type='GET')
        response = requests.get(url).json()
        request_log.response = response
        request_log.save()
        self.city = response['city']
        self.state = response['state']

    def get_premium(self):
        url = self._host % 'mediclaim/get_premium'
        data = dict(
            health_pay_mode=self.pay_mode,
            health_pay_type=self.health_pay_type,
            health_pay_type_text=self.health_pay_type_text,
            health_sum_insured=self.suminsured,
            health_pay_mode_text=self.pay_mode_text,
            health_me=self.health_me,
            gender_age=self.gender_ages,
            pincode=self.pincode,
            health_insu_id=self.insurer_code,
            health_sum_insured_range=[self.suminsured, self.suminsured],
            health_city_id=self.city_code or '',
            health_state_id=self.state_code or ''
        )
        request_log = ApplicationRequestLog.objects.create(
            application_id=self.reference_app.id, url=url, request_type='POST',
            payload=data)
        response = requests.post(url, data=data)
        request_log.response = response
        request_log.save()

    def generate_quote_id(self):
        url = self._host % 'save_quote_data'
        import json
        data = dict(
            section=self.section,
            quote_data=json.dumps(dict(
                health_pay_mode=self.pay_mode,
                health_pay_mode_text=self.pay_mode_text,
                health_me=self.health_me, health_pay_type=self.health_pay_type,
                health_pay_type_text=self.health_pay_type_text,
                health_sum_insured=self.suminsured,
                pincode=self.pincode, gender_age=self.gender_ages,
                health_sum_insured_range=[self.suminsured, self.suminsured],
                spouse='', child='', child_data=list()
            )), quote=''
        )
        request_log = ApplicationRequestLog.objects.create(
            application_id=self.reference_app.id, url=url, request_type='POST',
            payload=data)
        response = requests.post(url, data=data).json()
        request_log.response = response
        request_log.save()
        self.quote_id = response['quote']

    def get_products(self):
        url = (self._host % 'mediclaim/get_products/%s') % self.quote_id
        data = dict(quote=self.quote_id)
        ApplicationRequestLog.objects.create(
            application_id=self.reference_app.id, url=url, request_type='POST',
            payload=data)
        response = requests.post(url, data=data)
        return response

    def get_quote_data(self):
        self.get_products()
        import requests
        url = (self._host % 'get_quote_data/%s') % self.quote_id
        log = ApplicationRequestLog.objects.create(
            application_id=self.reference_app.id, url=url, request_type='GET',)
        response = requests.get(url).json()
        log.response = response
        log.save()
        self.city_code = response['data']['health_city_id']
        self.state_code = response['data']['health_state_id']
        self.fetch_quote_details()

    def fetch_quote_details(self):
        url = (self._host % 'mediclaim/fetch_quote/%s') % self.quote_id
        log = ApplicationRequestLog.objects.create(
            application_id=self.reference_app.id, url=url, request_type='GET')
        response = requests.get(url).json()
        log.response = response
        log.save()
        self.raw_quote = self.get_live_quote(response['quote_data'])
        self.premium = self.raw_quote['total_premium']
        self.company_name = re.sub('[ .]', '', self.raw_quote['company_name'])
        reference_app = self.reference_app
        reference_app.premium = self.raw_quote['total_premium']
        reference_app.save()

    def get_live_quote(self, quote_data):
        data = filter(lambda product: product[
            'company_name'] == Constant.COMPANY_NAME.get(
                self.reference_app.quote.premium.product_variant.company_category.company.name # noqa
            ), quote_data)
        quote = next(data)
        premium = int(self.reference_app.premium)
        while int(quote['total_premium']) not in range(
                premium - 100, premium + 100):
            quote = next(data)
        return quote

    def get_user_id(self):
        if self.user_id:
            return self.user_id
        url = self._host % 'save_user_info'
        app = self.reference_app
        data = dict(
            first_name=app.client.first_name,
            dob=app.client.dob.strftime('%d-%M-%Y'),
            last_name=app.client.last_name, email=app.client.email,
            gender=Constant.GENDER.get(app.client.gender, 'M'),
            mobile_no=app.client.phone_no, alternate_mobile='',
            occupation=Constant.OCCUPATION_CODE[app.client.occupation],
            pincode=self.pincode, city=self.city, state=self.state,
            address=app.client.address.full_address, user_id='',
            dealstage=self.dealstage, insu_id=self.insurer_code,
            insurance_type=self.section.title() + ' Insurance',
            amount=self.premium
        )
        log = ApplicationRequestLog.objects.create(
            application_id=self.reference_app.id, url=url, request_type='GET')
        response = requests.post(url, data=data).json()
        log.response = response
        log.save()
        return response['user_id']

    def insurer_operation(self):
        self.user_id = self.get_user_id()
        self.save()
        self.insurer_product.perform_creation()
        self.send_payment_link()
        return True

    @cached_property
    def health_me(self):
        gender_ages = list()
        for member in self.reference_app.active_members.exclude(
                relation='self'):
            gender_ages.append([
                ('M' if member.gender == 'male' else 'F'), str(member.age)])
        return gender_ages

    @cached_property
    def proposer(self):
        self.self_insured = False
        proposers = self.reference_app.active_members
        if proposers.filter(relation='self').exists():
            self.self_insured = True
            proposer = proposers.get(relation='self')
        elif proposers.filter(relation='spouse').exists():
            proposer = proposers.get(relation='spouse')
        else:
            proposer = proposers.first()
        proposer.marital_status = Constant.get_marital_status(
            proposer.relation) or self.reference_app.client.marital_status.title() # noqa
        return proposer

    @cached_property
    def health_pay_type(self):
        if self.reference_app.active_members.count() == 1:
            return ''
        return '%sA%sC' % (
            self.reference_app.adults, self.reference_app.childrens)

    @cached_property
    def health_pay_type_text(self):
        pay_type_text = ''
        if self.reference_app.active_members.count() == 1:
            return pay_type_text
        if self.reference_app.active_members.filter(relation='self').exists():
            pay_type_text += 'ME '
        if self.reference_app.active_members.filter(relation='spouse').exists(): # noqa
            pay_type_text += 'Spouse '
        if self.reference_app.active_members.filter(relation__in=['son', 'daughter']).exists(): # noqa
            pay_type_text += '%sChild' % self.reference_app.childrens
        return pay_type_text.strip()

    @cached_property
    def pay_mode(self):
        return 'I' if len(self.reference_app.active_members) == 1 else 'F'

    @cached_property
    def pay_mode_text(self):
        return 'Individual' if len(
            self.reference_app.active_members) == 1 else 'Family'

    @cached_property
    def gender_ages(self):
        return [[Constant.GENDER[self.proposer.gender], self.proposer.age]]

    @cached_property
    def all_premiums(self):
        return self.raw_quote['all_premium'].split(',')

    @cached_property
    def insurer_code(self):
        return self.raw_quote['insurance_code']

    def __str__(self):
        return '%s | %s' % (self.quote_id, self.reference_app.__str__())
