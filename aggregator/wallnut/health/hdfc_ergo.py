from payment.models import ApplicationRequestLog

from aggregator import Constant
import requests
import json


class HDFCERGOHealthInsurance(object):

    def __init__(self, wallnut):
        self.wallnut = wallnut
        self.application = wallnut.reference_app

    def get_payment_link(self):
        from goplannr.settings import ENV
        return '%s://payment.%s/health/hdfcergo/%s' % (
            'http' if ENV == 'localhost:8000' else 'https',
            ENV, self.wallnut.id)

    def perform_creation(self):
        self.save_proposal_data()
        self.accept_terms()
        self.wallnut.regenerate_payment_link = False
        self.wallnut.save()

    def save_proposal_data(self):
        data = self.get_data()
        url = self.wallnut._host % Constant.HDFC_ERGO_PROPOSAL_URL
        log = ApplicationRequestLog.objects.create(
            application_id=self.application.id, url=url, request_type='POST',
            payload=data)
        response = requests.post(url, data=data).json()
        log.response = response
        log.save()
        self.wallnut.proposal_id = response['proposal_id']
        self.wallnut.customer_id = response['customer_id']
        return response

    def accept_terms(self):
        data = dict(
            customer_id=self.wallnut.customer_id,
            proposal_id=self.wallnut.proposal_id,
            section='health', company='hdfc_ergo'
        )
        url = self.wallnut._host % Constant.HDFC_ERGO_CHECK_PROPOSAL_DATE_URL
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
            city_id=self.wallnut.city_code, me=self.wallnut.health_me,
            insu_id=self.wallnut.insurer_code,
            pay_mode=self.wallnut.pay_mode,
            pay_mode_text=self.wallnut.pay_mode_text,
            policy_period=1, pay_type=self.wallnut.health_pay_type,
            pay_type_text=self.wallnut.health_pay_type_text,
            premium=self.wallnut.raw_quote['all_premium'],
            quote=self.wallnut.quote_id,
            quote_refresh='N', state_id=self.wallnut.state_code,
            sum_insured=self.wallnut.suminsured,
            sum_insured_range=[
                self.wallnut.suminsured, self.wallnut.suminsured],
            user_id=self.wallnut.user_id, Address2='', Address3='',
            ApplFirstName=self.wallnut.proposer.first_name,
            ApplLastName=self.wallnut.proposer.last_name,
            ApplGender=Constant.GENDER.get(self.wallnut.proposer.gender),
            ApplDOB=self.wallnut.proposer.dob.strftime('%d-%m-%Y'),
            UIDNo=self.application.client.kycdocument_set.filter(
                document_type='aadhaar_card').last() or '000000000000',
            EmailId=self.application.client.email,
            MobileNo=self.application.client.phone_no,
            PhoneNo='', Address1='ST bed Layout, Kormamongala',
            Pincode=self.application.client.address.pincode.pincode,
            State=self.wallnut.state, City=self.city_mapper(self.wallnut.city),
            local_data_values=json.dumps(dict(
                health_city_id=self.wallnut.city_code,
                health_insu_id=self.wallnut.insurer_code,
                health_me=self.wallnut.health_me,
                health_pay_mode=self.wallnut.pay_mode,
                health_pay_mode_text=self.wallnut.pay_mode_text,
                health_pay_type=self.wallnut.health_pay_type,
                health_policy_period=1,
                health_premium=self.wallnut.raw_quote['all_premium'],
                health_quote=self.wallnut.quote_id,
                health_quote_refresh='N',
                health_state_id=self.wallnut.state_code,
                health_sum_insured=self.wallnut.suminsured,
                health_sum_insured_range=[
                    self.wallnut.suminsured, self.wallnut.suminsured],
                health_user_id=self.wallnut.user_id,
                gender_age=self.wallnut.gender_ages,
                pincode=self.application.client.address.pincode.pincode,
            )),
            disease1='N',
            insured_pattern=self.get_insurance_pattern(),
            TypeOfPlan='NF' if self.wallnut.pay_mode == 'I' else 'WF',
            coverType=self.wallnut.raw_quote['product_name'].replace(
                'Health Suraksha ', '').replace('Regain ', '')
        )
        nominee = self.application.nominee_set.filter(ignore=False).last()
        data.update(dict(
            NomineeRelationship=self.get_relationship_code(nominee.relation),
            NomineeName=nominee.get_full_name(),
            NomineeRelationship_text=self.get_relationship_text(
                nominee.relation))
        )
        count = 1
        for member in self.application.active_members.exclude(relation='self'):
            data.update(self.get_memeber_info(member, count))
            count += 1
        while count <= 3:
            data.update({
                'FirstName_%s' % count: '', 'LastName_%s' % count: '',
                'RelationShip_%s' % count: '', 'DOB_%s' % count: ''
            })
            count += 1

        return data

    def get_insurance_pattern(self):
        return {
            "I": "1000", "2A0C": "1100", "2A1C": "1110", "2A2C": "1120",
            "1A1C": "1010", "1A2C": "1020"}.get(
                self.wallnut.health_pay_type, '1000')

    def get_memeber_info(self, member, count):
        return {
            'FirstName_%s' % count: member.first_name,
            'LastName_%s' % count: member.last_name,
            'RelationShip_%s' % count: self.get_relationship_code(
                member.relation),
            'DOB_%s' % count: member.dob.strftime('%d-%m-%Y'),
        }

    def get_relationship_code(self, relation):
        return dict(
            son='S', daughter='D', spouse='S', mother='P', father='P',
            sister='B', brother='B', cousin='B',
        )[relation]

    def get_relationship_text(self, relation):
        return dict(
            son='Child', daughter='Child', spouse='Spouse',
            mother='Parent', father='Parent',
            sister='Sibling', brother='Sibling', cousin='Sibling',
        )[relation]

    def city_mapper(self, city):
        return dict(Bangalore='BENGALURU').get(city, city)
