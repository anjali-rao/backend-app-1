from utils.models import BaseModel, models
from broker import constant as Constant


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
    city = models.CharField(max_length=16, null=True)
    state = models.CharField(max_length=16, null=True)
    pincode = models.CharField(max_length=16, null=True)

    def save(self, *args, **kwargs):
        try:
            self.__class__.objects.get(pk=self.id)
        except self.__class__.DoesNotExist:
            self.handle_creation()
        super(self.__class__, self).save(*args, **kwargs)

    def handle_creation(self):
        self.get_state_city()
        self.generate_quote_id()
        self.section = Constant.SECTION.get(
            self.reference_app.application_type)
        self.suminsured = self.reference_app.suminsured
        self.premium = self.reference_app.premium

    def get_state_city(self):
        import requests
        url = self._host % (
            'health/proposal_aditya_birla/get_state_city?Pincode=%s') % (
                self.reference_app.quote.lead.pincode
        )
        response = requests.get(url).json()
        self.city = response['city']
        self.state = response['state']

    def generate_quote_id(self):
        import requests
        url = self._host % 'save_quote_data'
        data = dict(
            section=self.section,
            quote_data=dict(
                health_pay_mode='I',
                health_pay_mode_text='Individual',
                health_me=list(), health_pay_type='',
                health_pay_type_text='', health_sum_insured=self.suminsured,
                pincode=self.pincode, gender_age=[['M', '22']],
                health_sum_insured_range=['1500000', '1500000'],
                spouse='', child='', child_data=list()
            ), quote=''
        )
        response = requests.post(url, data=data).json()
        self.quote_id = response['quote']

    def get_quote_data(self):
        import requests
        url = (self._host % 'get_quote_data/%s') % self.quote_id
        response = requests.get(url)
        self.city_code = response['data']['health_city_id']
        self.state_code = response['data']['health_state_id']
        quotes = response['data']['quote_data']['response']
