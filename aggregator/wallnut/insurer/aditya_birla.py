from aggregator import Constant
import requests
import json


class AdityaBirlaHealthInsurance(object):
    proposal_url = 'health/proposal_aditya_birla/save_proposal_data' # noqa
    submit = 'health/proposal_aditya_birla/proposal_submit'

    def __init__(self, wallnut):
        self.wallnut = wallnut
        self.application = wallnut.reference_app

    def save_proposal_data(self):
        data = dict(
            city_id=self.wallnut.city_code, me=list(),
            insu_id=self.wallnut.insurer_code,
            pay_mode=self.wallnut.pay_mode,
            pay_mode_text=self.wallnut.pay_mode_text,
            policy_period=1, pay_type='', pay_type_text='',
            premium=self.wallnut.all_premiums,
            quote=self.wallnut.quote_id,
            quote_refresh='N', state_id=self.wallnut.state_code,
            sum_insured=self.wallnut.suminsured,
            sum_insured_range=[
                self.wallnut.suminsured, self.wallnut.sum_insured],
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
            proposer_Weight=self.wallnut.proposer.Weight,
            proposer_OccupationCode=Constant.OCCUPATION_CODE[
                self.wallnut.proposer.occupation],
            proposer_AnnualIncome=self.application.client.annual_income,
            proposer_PanNumber=self.application.client.kycdocument_set.filter(
                document_type='pancard').last() or '',
            proposer_AadhaarNo=self.application.client.kycdocument_set.filter(
                document_type='aadhaar_card').last() or '000000000000',
            proposer_AddressLine1=self.application.client.address.full_address,
            proposer_AddressLine2='', proposer_AddressLine3='',
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
                health_me=[], health_pay_mode=self.wallnut.health_pay_mode,
                health_pay_mode_text=self.wallnut.health_pay_mode_text,
                health_pay_type='', health_policy_period=1,
                health_premium=self.wallnut.premium,
                health_quote=self.wallnut.quote_id,
                health_quote_refresh='N',
                health_state_id=self.wallnut.state_code,
                health_sum_insured=self.wallnut.suminsured,
                health_sum_insured_range=self.wallnut.all_premiums,
                health_user_id=self.wallnut.user_id,
                gender_age=self.wallnut.gender_age
            )),
            NomineeName='',
            RelationToProposerCode='',
            nominee_add_same_as_proposer_add='Y',
            nominee_AddressLine1='',
            nominee_AddressLine2='',
            nominee_AddressLine3='',
            nominee_PinCode='560034',
            nominee_Country='IN',
            nominee_StateCode='KARNATAKA',
            nominee_TownCode='Bangalore',
            Namefor80D='R001', super_ncb='N',
            reload_sum_insured='N', room_upgrade='N', disease1='N',
            Doctorname='', ContactDetails='', lifestyle_ques='')
        count = 1
        for member in self.application.active_members:
            data.update(self.get_memeber_info(member, count))
            count += 1
        url = self.application % self.proposal_url
        response = requests.post(url, data=data)
        return response

    def submit_proposal(self):
        pass

    def get_memeber_info(self, member, count):
        return {
            'FirstName_%s' % count: member.first_name,
            'MiddleName_%s' % count: '',
            'LastName_%s' % count: member.last_name,
            'GenderCode_%s' % count: Constant.GENDER.get(member.gender),
            'BirthDate_%s' % count: member.dob.strftime('%d-%m-%Y'),
            'OccupationCode_%s' % count: Constant.RELATION_CODE[
                member.relation],
            'Height_%s' % count: member.height,
            'Weight_%s' % count: member.weight,
            'Alcohol_%s' % count: '',
            'Smoking_%s' % count: '',
            'Pouches_%s' % count: '',
        }
