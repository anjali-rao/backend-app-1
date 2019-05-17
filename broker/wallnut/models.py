from django.contrib.postgres.fields import JSONField

from utils.models import BaseModel, models
from broker import constant as Constant
import requests


class Application(BaseModel):
    _host = 'https://wallnut.in/%s'
    reference_app = models.ForeignKey(
        'sales.application', on_delete=models.PROTECT)
    section = models.CharField(max_length=16)
    suminsured = models.CharField(max_length=16)
    premium = models.FloatField(default=0.0)
    insurance_type = models.CharField(max_length=16)
    quote_id = models.CharField(max_length=128, null=True)
    city_code = models.CharField(max_length=16, null=True)
    state_code = models.CharField(max_length=16, null=True)
    insurer_code = models.CharField(max_length=8, null=True)
    dealstage = models.CharField(max_length=16, null=True)
    user_id = models.CharField(max_length=16, null=True)
    proposer_id = models.CharField(max_length=32, null=True)
    city = models.CharField(max_length=16, null=True)
    state = models.CharField(max_length=16, null=True)
    pincode = models.CharField(max_length=16, null=True)
    raw_quote = JSONField(default=dict)
    raw_quote_data = JSONField(default=dict)
    all_premiums = models.CharField(null=True, max_length=32)

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
        gender_ages = list()
        for member in self.reference_app.active_members:
            gender_ages.append([
                ('M' if member.gender == 'male' else 'F'), str(member.age)])
        import json
        data = dict(
            section=self.section,
            quote_data=json.dumps(dict(
                health_pay_mode='I' if len(gender_ages) == 1 else 'F',
                health_pay_mode_text='Individual' if len(gender_ages) == 1 else 'Family', # noqa
                health_me=list(), health_pay_type='',
                health_pay_type_text='', health_sum_insured=self.suminsured,
                pincode=self.pincode, gender_age=gender_ages,
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
            first_name=app.client.first_name,
            last_name=app.client.last_name,
            email=app.client.email,
            gender=Constant.GENDER.get(app.client.gender, 'M'),
            mobile_no=app.client.phone_no, alternate_mobile='',
            occupation=Constant.OCCUPATION_CODE[app.client.occupation],
            dob=app.client.dob,
            pincode=self.pincode, city=self.city, state=self.state,
            address=app.client.address.full_address,
            dealstage=self.dealstage,
            insurance_type=self.section.title() + ' Insurance',
            Insu_id=self.insurer_code, user_id=''
        )
        response = requests.post(url, data=data)
        return response

    def __str__(self):
        return '%s | %s' % (self.quote_id, self.reference_app.__str__())
