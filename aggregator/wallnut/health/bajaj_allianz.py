from django.utils.timezone import now

from payment.models import ApplicationRequestLog

from aggregator import Constant
import requests
import json


class BajajAllianzGeneralInsurance(object):
    proposal_url = 'health/proposal_aditya_birla/save_proposal_data' # noqa
    proposal_submit_url = 'health/proposal_aditya_birla/proposal_submit'
    check_proposal_date_url = 'check_proposal_date'

    def __init__(self, wallnut):
        self.wallnut = wallnut
        self.application = wallnut.reference_app

    def perform_creation(self):
        self.save_proposal_data()
        self.wallnut.save()

    def save_proposal_data(self):
        data = self.get_data()
        url = self.wallnut._host % Constant.BAJAJ_ALLIANZ_GIC_PROPOSAL_URL
        log = ApplicationRequestLog.objects.create(
            application_id=self.application.id, url=url, request_type='POST',
            payload=data)
        response = requests.post(url, data=data).json()
        log.response = response
        log.save()
        response = requests.post(url, data=data).json()
        self.wallnut.proposal_id = next((
            i for i in response['return_data'].split('&') if 'proposal_id' in i
        ), None).split('=')[1]
        return response

    def submit_proposal(self):
        data = self.get_data()
        data['proposal_id'] = self.wallnut.proposal_id
        url = self.wallnut._host % Constant.BAJAJ_ALLIANZ_GIC_CHECK_PROPOSAL_DATE_URL # noqa
        log = ApplicationRequestLog.objects.create(
            application_id=self.application.id, url=url, request_type='POST',
            payload=data)
        response = requests.post(url, data=data).json()
        log.response = response
        log.save()
        self.wallnut.proposal_id2 = response['proposal_id']
        self.wallnut.customer_id = response['customer_id']
        return response

    def accept_terms(self):
        data = dict(
            customer_id=self.wallnut.customer_id,
            proposal_id=self.wallnut.proposal_id2,
            section='health', company='aditya_birla'
        )
        url = self.wallnut._host % self.check_proposal_date_url
        log = ApplicationRequestLog.objects.create(
            application_id=self.application.id, url=url, request_type='POST',
            payload=data)
        response = requests.post(url, data=data).json()
        log.response = response
        log.save()
        self.wallnut.payment_ready = True
        return response

    def get_data(self):
        data = dict(
            quote=self.wallnut.quote_id,
            sum_insured_range=[
                self.wallnut.suminsured, self.wallnut.suminsured],
            sum_insured=self.wallnut.suminsured,
            pay_mode_text=self.wallnut.pay_mode_text,
            me=self.wallnut.health_me, user_id=self.wallnut.user_id,
            insu_id=self.wallnut.insurer_code,
            premium=self.wallnut.all_premiums,
            policy_period=1, pay_type=self.wallnut.health_pay_type,
            pay_type_text=self.wallnut.health_pay_type_text,
            pay_mode=self.wallnut.pay_mode,
            pan_india='N', first_name=self.wallnut.proposer.first_name,
            surname=self.wallnut.proposer.last_name,
            sex=Constant.GENDER.get(self.wallnut.proposer.gender),
            dateOfBirth=self.wallnut.proposer.dob.strftime('%d-%m-%Y'),
            maritalstatus=self.get_marital_status(
                self.wallnut.proposer.marital_status),
            profession=self.get_profession_code(
                self.wallnut.proposer.occupation),
            email=self.application.client.email,
            phone_no=self.application.client.phone_no,
            addLine1=self.application.client.address.full_address,
            addLine2='', addLine3=self.city_mapper(self.wallnut.city),
            addLine4=self.wallnut.state.upper(),
            health_insu_id=self.wallnut.insurer_code,
            termStartDate=now().strftime('%d-%m-%Y'),
            extraColumn3=0, stringval8='N', stringval9='N',
            stringval10='N', stringval11='N',
            local_data_values=json.dumps(dict(
                health_sum_insured_range=self.wallnut.all_premiums,
                health_quote=self.wallnut.quote_id,
                health_sum_insured=self.wallnut.suminsured,
                health_pay_mode_text=self.wallnut.pay_mode_text,
                health_me=self.wallnut.health_me,
                health_user_id=self.wallnut.user_id,
                health_insu_id=self.wallnut.insurer_code,
                health_premium=self.wallnut.premium,
                health_policy_period=1,
                health_pay_type=self.wallnut.health_pay_type,
                health_pay_mode=self.wallnut.pay_mode,
                health_pay_type_text=self.wallnut.health_pay_type_text,
                gender_age=self.wallnut.gender_ages,
                pincode=self.wallnut.pincode)))

        count = 1
        for member in self.application.active_members:
            data.update(self.get_memeber_info(member, count))
            count += 1
        while count <= 6:
            data.update({
                'relation_%s' % count: '', 'FirstName_%s' % count: '',
                'LastName_%s' % count: '', 'gender_%s' % count: '',
                'dateOfBirth_%s' % count: '', 'occupation_%s' % count: '',
                'monthlyIncome_%s' % count: '', 'heightCm_%s' % count: '',
                'weightKg_%s' % count: '', 'NomineeName_%s' % count: '',
                'NomineeRelationship_%s' % count: ''})
            count += 1

        return data

    def get_memeber_info(self, member, count):
        member_details = {
            'relation_%s' % count: self.get_relationshio_code(member.relation),
            'FirstName_%s' % count: member.first_name,
            'LastName_%s' % count: member.last_name,
            'gender_%s' % count: member.gender,
            'dateOfBirth_%s' % count: member.dob.strftime('%d-%m-%Y'),
            'occupation_%s' % count: self.get_profession_code(
                member.occupation),
            'monthlyIncome_%s' % count: 0,
            'heightCm_%s' % count: member.height,
            'weightKg_%s' % count: member.weight,
            'NomineeName_%s' % count: '',
            'NomineeRelationship_%s' % count: ''
        }
        if count == 1:
            nominee = self.application.nominee_set.filter(ignore=False).last()
            member_details.update(dict(
                NomineeName_1=nominee.get_full_name(),
                NomineeRelationship_1=self.get_relationshion_code(
                    nominee.relation)))
        return member_details

    def get_profession_code(self, profession):
        dict(
            Business=1, Doctor=2, Housewife=3, Professor=4,
            Retired=5, Service=6, Student=7, Teacher=8, Unemployed=9,
            Other=10)[profession]

    def get_marital_status(self, maritalstatus):
        return dict(
            single='UNMARRIED', married='MARRIED'
        ).get(maritalstatus.lower(), 'UNMARRIED')

    def get_relationshion_code(self, relation):
        return dict(
            son='SON', daughter='DAUGHTER', spouse='SPOUSE', mother='MOTHER',
            father='FATHER', sister='SISTER', brother='BROTHER', self='SELF',
        ).get(relation, 'OTHERS')

    def city_mapper(self, city):
        return dict(Bangalore='BENGALURU').get(city, city)
