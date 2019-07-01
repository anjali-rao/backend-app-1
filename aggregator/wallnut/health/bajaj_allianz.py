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
        self.save_quote_data()
        self.save_proposal_data()
        self.accept_terms()
        self.wallnut.regenerate_payment_link = False
        self.wallnut.save()

    def get_payment_link(self):
        from goplannr.settings import ENV
        return '%s://payment.%s/health/bajajhealth/%s' % (
            'http' if ENV == 'localhost:8000' else 'https',
            ENV, self.wallnut.id)

    def save_quote_data(self):
        url = self.wallnut._host % 'save_quote_data'
        data = dict(
            section=self.wallnut.section,
            quote=self.wallnut.quote_id,
            user_id=self.wallnut.user_id,
            quote_data=json.dumps(dict(
                health_premium=self.wallnut.raw_quote['all_premium'],
                health_pay_mode=self.wallnut.pay_mode,
                health_pay_mode_text=self.wallnut.pay_mode_text,
                health_pay_type=self.wallnut.health_pay_type,
                health_pay_type_text=self.wallnut.health_pay_type_text,
                health_sum_insured=self.wallnut.suminsured,
                health_me=self.wallnut.health_me,
                gender_age=self.wallnut.gender_ages,
                pincode=self.wallnut.pincode,
                health_state_id=self.wallnut.state_code
            )))
        request_log = ApplicationRequestLog.objects.create(
            application_id=self.application.id, url=url, request_type='POST',
            payload=data)
        response = requests.post(url, data=data).json()
        request_log.response = response
        request_log.save()

    def save_proposal_data(self):
        data = self.get_data()
        url = self.wallnut._host % Constant.BAJAJ_ALLIANZ_GIC_PROPOSAL_URL
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
            section='health', company='aditya_birla'
        )
        url = self.wallnut._host % Constant.BAJAJ_ALLIANZ_GIC_CHECK_PROPOSAL_DATE_URL # noqa
        log = ApplicationRequestLog.objects.create(
            application_id=self.application.id, url=url, request_type='POST',
            payload=data)
        response = requests.post(url, data=data).json()
        log.response = response
        log.save()
        self.wallnut.payment_ready = True
        return response

    def get_data(self):
        proposer = self.application.proposer
        data = dict(
            quote_refresh='N', state_id=self.wallnut.state_code,
            city_id=self.wallnut.city_code, quote=self.wallnut.quote_id,
            sum_insured_range=[
                self.wallnut.suminsured, self.wallnut.suminsured],
            sum_insured=self.wallnut.suminsured,
            pay_mode_text=self.wallnut.pay_mode_text,
            me=self.wallnut.health_me, user_id=self.wallnut.user_id,
            insu_id=self.wallnut.insurer_code,
            premium=','.join(self.wallnut.all_premiums),
            policy_period=1, pay_type=self.wallnut.health_pay_type,
            pay_type_text=self.wallnut.health_pay_type_text,
            pay_mode=self.wallnut.pay_mode,
            pan_india='N', firstName=self.wallnut.proposer.first_name,
            surname=self.wallnut.proposer.last_name,
            sex=Constant.GENDER.get(self.wallnut.proposer.gender),
            dateOfBirth=self.wallnut.proposer.dob.strftime('%d-%m-%Y'),
            maritalstatus=self.get_marital_status(
                self.wallnut.proposer.marital_status),
            profession=self.get_profession_code(
                self.wallnut.proposer.occupation),
            email=proposer.email,
            mobile=proposer.phone_no,
            addLine1=proposer.address.full_address[:40],
            addLine2=proposer.address.full_address[41:],
            addLine3=self.city_mapper(self.wallnut.city),
            addLine4=self.wallnut.state.upper(),
            health_insu_id=self.wallnut.insurer_code,
            termStartDate=now().strftime('%d-%m-%Y'),
            extraColumn3='0', stringval8='N', stringval9='N',
            stringval10='N', stringval11='N',
            Pincode=proposer.address.pincode.pincode)
        count = 1

        local_data_values = 'health_pay_mode=%s#health_state_id=%s#health_quote_refresh=N#health_sum_insured=%s#health_premium=%s#health_insu_id=14#health_sum_insured_range=%s#health_user_id=14252#health_policy_period=1#health_pay_type=%s#health_pay_mode_text=%s#health_quote=%s#health_city_id=%s#health_pay_type_text=%s#health_me=%s#gender_age=%s#pincode=%s' % ( # noqa
            self.wallnut.pay_mode, self.wallnut.state_code, self.wallnut.suminsured, self.wallnut.raw_quote['all_premium'], [self.wallnut.suminsured, self.wallnut.suminsured], self.wallnut.health_pay_type, self.wallnut.pay_mode_text, self.wallnut.quote_id, self.wallnut.city_code, self.wallnut.health_pay_type_text, self.wallnut.health_me, self.wallnut.gender_ages, self.wallnut.pincode # noqa
        )
        data['local_data_values'] = local_data_values
        init_count = 1
        for member in self.application.active_members:
            data.update(self.get_memeber_info(member, count))
            count += 1
        data[''] = ''
        while count <= 6:
            if count is not 2:
                init_count += 1
            relation = 'SPOUSE' if count is 2 else 'CHILD %s' % init_count
            data.update({
                'relation_%s' % count: relation, 'FirstName_%s' % count: '',
                'LastName_%s' % count: '', 'gender_%s' % count: '',
                'dateOfBirth_%s' % count: '', 'occupation_%s' % count: '',
                'monthlyIncome_%s' % count: '', 'heightCm_%s' % count: '',
                'weightKg_%s' % count: '', 'NomineeName_%s' % count: '',
                'NomineeRelationship_%s' % count: ''})
            count += 1

        return data

    def get_memeber_info(self, member, count):
        member_details = {
            'relation_%s' % count: self.get_relationship_code(member.relation),
            'FirstName_%s' % count: member.first_name,
            'LastName_%s' % count: member.last_name,
            'gender_%s' % count: Constant.GENDER.get(member.gender),
            'dateOfBirth_%s' % count: member.dob.strftime('%d-%m-%Y'),
            'occupation_%s' % count: self.get_profession_code(
                member.occupation),
            'monthlyIncome_%s' % count: '',
            'heightCm_%s' % count: str(int(member.height)),
            'weightKg_%s' % count: str(int(member.weight)),
            'NomineeName_%s' % count: '',
            'NomineeRelationship_%s' % count: ''
        }
        if count == 1:
            nominee = self.application.nominee_set.filter(ignore=False).last()
            member_details.update(dict(
                NomineeName_1=nominee.get_full_name(),
                NomineeRelationship_1=self.get_relationship_code(
                    nominee.relation),
                monthlyIncome_1=str(int(Constant.INCOME.get(
                    self.application.proposer.annual_income) / 12))
            ))
        return member_details

    def get_profession_code(self, profession):
        return dict(
            self_employed_or_business=1, doctor=2, Housewife=3, Professor=4,
            retired=5, salaried=6, Student=7, Teacher=8, unemployed=9,
            others=10).get(profession, 10)

    def get_marital_status(self, maritalstatus):
        return dict(
            single='UNMARRIED', married='MARRIED'
        ).get(maritalstatus.lower(), 'UNMARRIED')

    def get_relationship_code(self, relation):
        return dict(
            son='SON', daughter='DAUGHTER', spouse='SPOUSE', mother='MOTHER',
            father='FATHER', sister='SISTER', brother='BROTHER', self='SELF',
        ).get(relation, 'OTHERS')

    def city_mapper(self, city):
        return city.upper()
