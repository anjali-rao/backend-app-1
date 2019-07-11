from payment.models import ApplicationRequestLog

from aggregator import Constant
import requests
import json


class ApolloMunichHealthInsurance(object):
    payment_url = 'https://pg-abhi.adityabirlahealth.com/ABHIPGIntegration/ABHISourceLanding.aspx' # noqa

    def __init__(self, wallnut):
        self.wallnut = wallnut
        self.application = wallnut.reference_app

    def get_payment_link(self):
        from goplannr.settings import ENV
        return '%s://payment.%s/health/adityabirla/%s' % (
            'http' if ENV == 'localhost:8000' else 'https',
            ENV, self.wallnut.id)

    def perform_creation(self):
        self.save_proposal_data()
        self.submit_proposal()
        self.accept_terms()
        self.wallnut.save()

    def save_proposal_data(self):
        data = self.get_data()
        url = self.wallnut._host % Constant.ADITYA_BIRAL_PROPOSAL_URL
        log = ApplicationRequestLog.objects.create(
            application_id=self.application.id, url=url, request_type='POST',
            payload=data)
        response = requests.post(url, data=data).json()
        log.response = response
        log.save()
        self.wallnut.proposal_id = next((
            i for i in response['return_data'].split('&') if 'proposal_id' in i
        ), None).split('=')[1]
        return response

    def submit_proposal(self):
        data = self.get_data()
        data['proposal_id'] = self.wallnut.proposal_id
        url = self.wallnut._host % Constant.ADITYA_BIRAL_PROPOSAL_SUBMIT_URL
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
        url = self.wallnut._host % Constant.ADITYA_BIRLA_CHECK_PROPOSAL_DATE_URL # noqa
        log = ApplicationRequestLog.objects.create(
            application_id=self.application.id, url=url, request_type='POST',
            payload=data)
        response = requests.post(url, data=data).json()
        log.response = response
        log.save()
        self.wallnut.payment_ready = True
        return response

    def get_data(self):
        pan_no = self.application.client.proposerdocument_set.filter(
            document_type='pancard', ignore=False).last()
        proposer_pannumber = pan_no.document_number if pan_no else ''
        aadhar_no = self.application.client.proposerdocument_set.filter(
            document_type='aadhaar_card', ignore=False).last()
        proposer_aadhar_no = aadhar_no.document_number if aadhar_no else ''
        address = self.application.client.address.full_address
        data = dict(
            city_id=self.wallnut.city_code, me=self.wallnut.health_me,
            insu_id=self.wallnut.insurer_code,
            pay_mode=self.wallnut.pay_mode,
            pay_mode_text=self.wallnut.pay_mode_text,
            policy_period=1, pay_type=self.wallnut.health_pay_type,
            pay_type_text=self.wallnut.health_pay_type_text,
            premium=self.wallnut.all_premiums,
            quote=self.wallnut.quote_id,
            quote_refresh='N', state_id=self.wallnut.state_code,
            sum_insured=self.wallnut.suminsured,
            sum_insured_range=[
                self.wallnut.suminsured, self.wallnut.suminsured],
            user_id=self.wallnut.user_id,
            proposer_FirstName=self.wallnut.proposer.first_name,
            proposer_MiddleName='',
            proposer_LastName=self.wallnut.proposer.last_name,
            proposer_GenderCode=Constant.GENDER.get(
                self.wallnut.proposer.gender),
            proposer_MaritalStatusCode=self.wallnut.proposer.marital_status,
            proposer_BirthDate=self.wallnut.proposer.dob.strftime('%d-%m-%Y'),
            proposer_Email=self.application.client.email,
            proposer_Number=self.application.client.phone_no,
            proposer_Height=self.wallnut.proposer.height,
            proposer_Weight=self.wallnut.proposer.weight,
            proposer_OccupationCode=Constant.OCCUPATION_CODE.get(
                self.wallnut.proposer.occupation, 'O009'),
            proposer_AnnualIncome=Constant.INCOME.get(
                self.application.client.annual_income) or 500000,
            proposer_PanNumber=proposer_pannumber,
            proposer_AadhaarNo=proposer_aadhar_no,
            proposer_AddressLine1=address[:50],
            proposer_AddressLine2=address[51:], proposer_AddressLine3='',
            proposer_PinCode=self.application.client.address.pincode.pincode,
            proposer_Country='Indian', proposer_StateCode=self.wallnut.state,
            proposer_TownCode=self.wallnut.city,
            self_insured=self.wallnut.self_insured,
            SumAssured=self.wallnut.suminsured,
            health_insu_id=self.wallnut.insurer_code,
            health_pay_mode=self.wallnut.pay_mode,
            insured_pattern='', customer_id='', proposal_id='',
            pincode=self.application.client.address.pincode.pincode,
            local_data_values=json.dumps(dict(
                health_city_id=self.wallnut.city_code,
                health_insu_id=self.wallnut.insurer_code,
                health_me=self.wallnut.health_me,
                health_pay_mode=self.wallnut.pay_mode,
                health_pay_mode_text=self.wallnut.pay_mode_text,
                health_pay_type=self.wallnut.health_pay_type,
                health_pay_type_text=self.wallnut.health_pay_type_text,
                health_policy_period=1,
                health_premium=self.wallnut.premium,
                health_quote=self.wallnut.quote_id,
                health_quote_refresh='N',
                health_state_id=self.wallnut.state_code,
                health_sum_insured=self.wallnut.suminsured,
                health_sum_insured_range=self.wallnut.all_premiums,
                health_user_id=self.wallnut.user_id,
                gender_age=self.wallnut.gender_ages
            )),
            nominee_add_same_as_proposer_add='Y',
            nominee_AddressLine1=self.application.client.address.full_address,
            nominee_AddressLine2='',
            nominee_AddressLine3='',
            nominee_PinCode=self.wallnut.pincode,
            nominee_Country='IN',
            nominee_StateCode=self.wallnut.state,
            nominee_TownCode=self.wallnut.city,
            Namefor80D='R001', super_ncb='N',
            reload_sum_insured='N', room_upgrade='N', disease1='N',
            Doctorname='', ContactDetails='', lifestyle_ques='')
        nominee = self.application.nominee_set.filter(ignore=False).last()
        data.update(dict(
            NomineeName=nominee.get_full_name(),
            RelationToProposerCode=Constant.RELATION_CODE[nominee.relation]))
        count = 1
        for member in self.application.active_members:
            data.update(self.get_memeber_info(member, count))
            count += 1
        while count <= 6:
            data.update({
                'FirstName_%s' % count: '', 'MiddleName_%s' % count: '',
                'LastName_%s' % count: '', 'GenderCode_%s' % count: '',
                'RelationshipCode_%s' % count: '',
                'MaritalStatusCode_%s' % count: '',
                'OccupationCode_%s' % count: '', 'Height_%s' % count: '',
                'Weight_%s' % count: '', 'Alcohol_%s' % count: '',
                'Smoking_%s' % count: '', 'Pouches_%s' % count: '',
            })
            count += 1

        return data

    def get_memeber_info(self, member, count):
        return {
            'FirstName_%s' % count: member.first_name,
            'MiddleName_%s' % count: '',
            'LastName_%s' % count: member.last_name,
            'GenderCode_%s' % count: Constant.GENDER.get(member.gender),
            'BirthDate_%s' % count: member.dob.strftime('%d-%m-%Y'),
            'RelationshipCode_%s' % count: Constant.RELATION_CODE[
                member.relation],
            'MaritalStatusCode_%s' % count: Constant.get_marital_status(
                member.relation) or self.wallnut.proposer.marital_status,
            'OccupationCode_%s' % count: Constant.OCCUPATION_CODE.get(
                member.occupation, 'O009'),
            'Height_%s' % count: member.height,
            'Weight_%s' % count: member.weight,
            'Alcohol_%s' % count: '',
            'Smoking_%s' % count: '',
            'Pouches_%s' % count: '',
        }

