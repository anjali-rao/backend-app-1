from django.contrib.postgres.fields import JSONField
from django.utils.functional import cached_property

from utils.models import BaseModel, models
from aggregator import Constant
from aggregator.wallnut import evaluateClassName
import requests


class Application(BaseModel):
    _host = 'https://wallnut.in/%s'
    reference_app = models.ForeignKey(
        'sales.application', on_delete=models.PROTECT)
    section = models.CharField(max_length=16)
    company_name = models.CharField(max_length=32, null=True)
    suminsured = models.CharField(max_length=16)
    premium = models.FloatField(default=0.0)
    insurance_type = models.CharField(max_length=16)
    quote_id = models.CharField(max_length=128, null=True)
    city_code = models.CharField(max_length=16, null=True)
    state_code = models.CharField(max_length=16, null=True)
    dealstage = models.CharField(max_length=32, null=True)
    user_id = models.CharField(max_length=16, null=True)
    proposer_id = models.CharField(max_length=32, null=True)
    city = models.CharField(max_length=16, null=True)
    state = models.CharField(max_length=16, null=True)
    pincode = models.CharField(max_length=16, null=True)
    raw_quote = JSONField(default=dict)
    raw_quote_data = JSONField(default=dict)

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.insurer_product = evaluateClassName(self.company_name)(self)

    def save(self, *args, **kwargs):
        try:
            self.__class__.objects.get(pk=self.id)
        except self.__class__.DoesNotExist:
            self.handle_creation()
        super(self.__class__, self).save(*args, **kwargs)

    def handle_creation(self):
        self.section = Constant.SECTION.get(
            self.reference_app.application_type)
        self.suminsured = self.reference_app.suminsured
        self.premium = self.reference_app.premium
        self.pincode = self.reference_app.quote.lead.pincode
        self.dealstage = 'productshortlisted'
        self.get_state_city()
        self.generate_quote_id()
        self.get_quote_data()

    def get_state_city(self):
        url = self._host % (
            'health/proposal_aditya_birla/get_state_city?Pincode=%s') % (
                self.reference_app.quote.lead.pincode
        )
        response = requests.get(url).json()
        self.city = response['city']
        self.state = response['state']

    def generate_quote_id(self):
        url = self._host % 'save_quote_data'
        import json
        data = dict(
            section=self.section,
            quote_data=json.dumps(dict(
                health_pay_mode=self.pay_mode,
                health_pay_mode_text=self.pay_mode_text,
                health_me=list(), health_pay_type='',
                health_pay_type_text='', health_sum_insured=self.suminsured,
                pincode=self.pincode, gender_age=self.gender_ages,
                health_sum_insured_range=[self.suminsured, self.suminsured],
                spouse='', child='', child_data=list()
            )), quote=''
        )
        response = requests.post(url, data=data).json()
        self.quote_id = response['quote']

    def get_products(self):
        url = (self._host % '/mediclaim/get_products/%s') % self.quote_id
        requests.post(url, data=dict(quote=self.quote_id))

    def get_quote_data(self):
        self.get_products()
        import requests
        url = (self._host % 'get_quote_data/%s') % self.quote_id
        response = requests.get(url).json()
        self.city_code = response['data']['health_city_id']
        self.state_code = response['data']['health_state_id']
        self.fetch_quote_details()

    def fetch_quote_details(self):
        url = (self._host % 'mediclaim/fetch_quote/%s') % self.quote_id
        response = requests.get(url).json()
        self.raw_quote_data = response['quote_data']
        self.raw_quote = self.get_live_quote()
        self.premium = self.raw_quote['total_premium']
        self.insurer_code = self.raw_quote.get()
        self.company_name = ''.join(self.raw_quote['company_name'].split())
        reference_app = self.reference_app
        reference_app.premium = self.raw_quote['total_premium']
        reference_app.save()

    def get_live_quote(self):
        return next(filter(lambda product: product[
            'company_name'] == Constant.COMPANY_NAME.get(
                self.reference_app.quote.premium.product_variant.company_category.company.name # noqa
            ), self.raw_quote_data))

    def save_user_details(self):
        url = self._host % 'save_user_info'
        app = self.reference_app
        data = dict(
            first_name=app.client.first_name, dob=app.client.dob,
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
        response = requests.post(url, data=data)
        self.user_id = response['user_id']
        return response

    @cached_property
    def proposer(self):
        self.self_insured = False
        proposers = self.reference_app.active_members
        if proposers.filter(relation='self').exists():
            self.self_insured = True
            proposer = proposers.get(relation='self')
        elif proposers.filter(relation='spouse').exists:
            proposer = proposers.get(relation='spouse')
        else:
            proposer = proposers.first()
        if proposer.relation in ['son', 'daughter']:
            proposer.marital_status = 'Single'
        elif proposer.relation == 'self':
            proposer.marital_status = self.application.client.marital_status.title() # noqa
        else:
            proposer.marital_status = 'Married'
        return proposer

    @cached_property
    def pay_mode(self):
        return 'I' if len(self.gender_ages) == 1 else 'F',

    @cached_property
    def pay_mode_text(self):
        return 'Individual' if self.pay_mode == 'I' else 'Family',

    @cached_property
    def gender_ages(self):
        gender_ages = list()
        for member in self.reference_app.active_members:
            gender_ages.append([
                ('M' if member.gender == 'male' else 'F'), str(member.age)])
        return gender_ages

    @cached_property
    def all_premiums(self):
        return self.raw_quote['all_premium'].split(',')

    @cached_property
    def insurer_code(self):
        return self.raw_quote['insurance_code']

    def __str__(self):
        return '%s | %s' % (self.quote_id, self.reference_app.__str__())
