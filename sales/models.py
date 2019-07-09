# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from utils.models import BaseModel, models
from utils import (
    constants as Constants, get_choices, genrate_random_string)

from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.utils.functional import cached_property
from django.db.models.signals import post_save
from django.db import IntegrityError
from django.dispatch import receiver
from django.utils.timezone import now
from django.contrib.contenttypes.fields import GenericForeignKey

from questionnaire.models import Response
from utils.mixins import RecommendationException
from utils import get_proposer_upload_path
from goplannr.settings import ENV


class Quote(BaseModel):
    opportunity = models.ForeignKey(
        'crm.Opportunity', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(
        max_length=16, choices=Constants.STATUS_CHOICES,
        default='pending')
    limit = models.Q(app_label='product', model='healthpremium')
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, limit_choices_to=limit)
    premium_id = models.PositiveIntegerField()
    premium = GenericForeignKey('content_type', 'premium_id')
    recommendation_score = models.FloatField(default=0.0)
    ignore = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.__class__.objects.filter(
            opportunity_id=self.opportunity_id, premium_id=self.premium_id,
            ignore=False
        ).exclude(status='accepted').update(ignore=True)
        super(Quote, self).save(*args, **kwargs)

    def __str__(self):
        return '%s - %s' % (
            self.premium.amount,
            self.premium.product_variant.company_category.company.name)

    class Meta:
        ordering = ['-recommendation_score', ]

    def get_feature_details(self):
        variant = self.premium.product_variant
        features = variant.feature_set.all()
        if variant.parent:
            features = features | variant.parent.feature_set.exclude(
                feature_master__name__in=features.values_list(
                    'feature_master__name', flat=True))
        return features.order_by('feature_master__order').values(
            'feature_master__name', 'short_description',
            'feature_master__long_description')

    def get_faq(self):
        company_category = self.premium.product_variant.company_category
        return [dict(
            question='Claim settlement ratio',
            answer=company_category.claim_settlement),
            dict(question='Company details', answer='Name: %s\nWebsite: %s' % (
                company_category.company.name,
                company_category.company.website or '-'))]

    @cached_property
    def health_checkup(self):
        return 1500 * self.opportunity.category_opportunity.adults

    @cached_property
    def wellness_reward(self):
        return round(
            self.opportunity.category_opportunity.wellness_reward * self.premium.amount, 2) # noqa

    @cached_property
    def tax_saving(self):
        return round(
            self.opportunity.category_opportunity.tax_saving * self.premium.amount, 2) # noqa

    @cached_property
    def effective_premium(self):
        return round(self.premium.amount - (
            self.health_checkup + self.wellness_reward + self.tax_saving))


class Application(BaseModel):
    app_client = models.ForeignKey(
        'crm.Lead', on_delete=models.PROTECT, null=True, blank=True)
    reference_no = models.CharField(max_length=10, unique=True, db_index=True)
    premium = models.FloatField(default=0.0)
    suminsured = models.FloatField(default=0.0)
    proposer = models.ForeignKey(
        'crm.Contact', null=True, on_delete=models.PROTECT)
    application_type = models.CharField(
        max_length=32, choices=get_choices(Constants.APPLICATION_TYPES))
    quote = models.OneToOneField('sales.Quote', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=32, choices=Constants.APPLICATION_STATUS, default='fresh')
    stage = models.CharField(
        max_length=32, default='proposer_details',
        choices=get_choices(Constants.APPLICATION_STAGES))
    previous_policy = models.BooleanField(default=False)
    name_of_insurer = models.CharField(blank=True, max_length=128)
    proposer_verified = models.BooleanField(default=False)
    payment_failed = models.BooleanField(null=True, blank=True)
    payment_mode = models.CharField(max_length=64, choices=get_choices(
        Constants.AGGREGATOR_CHOICES), default='offline')
    terms_and_conditions = models.BooleanField(null=True)

    def save(self, *args, **kwargs):
        try:
            current = self.__class__.objects.get(pk=self.id)
            if self.status != current.status:
                self.handle_status_change(current)
            if (current.payment_failed != self.payment_failed and self.payment_failed) or self.status == 'completed': # noqa
                self.send_slack_notification()
        except self.__class__.DoesNotExist:
            self.generate_reference_no()
            self.application_type = self.company_category.category.name.lower(
            ).replace(' ', '')
        super(Application, self).save(*args, **kwargs)

    def handle_status_change(self, current):
        if self.status == 'submitted' and self.stage == 'completed':
            self.create_client()
            self.create_policy()
            self.create_commission(current)
        if current.status == 'fresh' and self.status == 'submitted':
            self.send_slack_notification()

    def send_slack_notification(self):
        mode = 'Offline + Online'
        if self.quote.opportunity.lead.user.user_type == 'subscriber':
            event = 'Application created and payment process done'
            mode = 'Subscriber'
        elif self.payment_mode == 'offline':
            event = 'Application created and payment process done'
            mode = 'Offline'
        elif self.payment_failed:
            event = Constants.PAYMENT_ERROR
        else:
            event = Constants.PAYMENT_SUCCESS
        self.send_slack_request(event, mode)

    def aggregator_operation(self):
        premium = self.quote.premium
        if not premium.product_variant.online_process or not premium.online_process:  # noqa
            return False
        self.status = 'payment_due'
        from aggregator.wallnut.models import Application as Aggregator
        if not hasattr(self, 'application'):
            Aggregator.objects.create(
                reference_app_id=self.id,
                insurance_type=self.application_type)
            self.payment_mode = 'wallnut'
        self.save()
        return self.payment_mode != 'offline'

    def update_fields(self, **kw):
        updated = False
        for field in kw.keys():
            setattr(self, field, kw[field])
            if not updated:
                updated = True
        if updated:
            self.save()

    def generate_reference_no(self):
        self.reference_no = genrate_random_string(10)
        if self.__class__.objects.filter(
                reference_no=self.reference_no).exists():
            while self.__class__.objects.filter(
                    reference_no=self.reference_no).exists():
                self.reference_no = genrate_random_string(10)

    def add_default_members(self):
        category_opportunity = self.quote.opportunity.category_opportunity
        today = now()
        members = list()

        def get_member_instance(gender, relation, dob=None):
            instance = Member(
                application_id=self.id, dob=dob,
                relation=relation, gender=gender)
            if relation == 'self':
                responses = Response.objects.filter(
                    question__category_id=self.company_category.category.id,
                    opportunity_id=category_opportunity.opportunity_id)
                occupation_res = responses.filter(question__title='Occupation')
                if occupation_res.exists():
                    instance.occupation = responses.latest('created').answer.answer.replace(' ', '_').lower() # noqa
            return instance

        for member, age in category_opportunity.family.items():
            member = member.split('_')[0]
            gender = category_opportunity.gender if member == 'self' else 'male' # noqa
            if member == 'spouse':
                gender = 'male' if category_opportunity.gender == 'female' else 'female' # noqa
            elif member == 'mother':
                gender = 'female'
            elif member in ['son', 'daughter']:
                while age > 0:
                    members.append(get_member_instance(
                        ('male' if member == 'son' else 'female'), member))
                    age -= 1
                continue
            instance = get_member_instance(gender, member, '%s-%s-%s' % (
                today.year - int(age), today.month, today.day))
            members.append(instance)
        Member.objects.bulk_create(members)

    def verify_proposer(self, otp):
        from django.core.cache import cache
        response = otp == cache.get('APP-%s:' % self.reference_no)
        cache.delete('APP-%s:' % self.reference_no)
        return response

    def send_propser_otp(self):
        from users.models import Account
        Account.send_otp('APP-%s:' % self.reference_no, self.proposer.phone_no)

    def create_policy(self):
        return Policy.objects.get_or_create(application_id=self.id)

    def invalidate_cache(self):
        from django.core.cache import cache
        cache.delete('USER_CART:%s' % self.quote.opportunity.lead.user_id)
        cache.delete('USER_CONTACTS:%s' % self.quote.opportunity.lead.user_id)
        cache.delete('USER_EARNINGS:%s' % self.quote.opportunity.lead.user_id)

    def create_client(self, save=False):
        lead = self.quote.opportunity.lead
        if not lead.is_client:
            lead.is_client = True
            lead.save()
        self.app_client_id = lead.id

    def create_commission(self, current):
        from earnings.models import Commission
        cc = self.quote.premium.product_variant.company_category
        amount = self.quote.premium.commission + cc.company.commission + cc.category.commission + self.quote.opportunity.lead.user.enterprise.commission # noqa
        if not hasattr(self, 'commission'):
            commission = Commission(
                application_id=self.id, amount=self.premium * amount)
            if current.payment_failed != self.payment_failed and self.payment_failed is False: # noqa
                commission.status = 'application_submitted'
            commission.save()
            commission.updated = True
            commission.save()
            commission.earning.user.account.send_sms(
                commission.earning.get_earning_message(self))

    def send_slack_request(self, event, mode, mode_type='success'):
        import requests
        client = self.quote.opportunity.lead
        endpoint = 'https://hooks.slack.com/services/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' # noqa
        link = '%s://admin.%s/sales/application/%s/change/' % (
            'http' if ENV == 'localhost:8000' else 'https', ENV, self.id)
        data = dict(
            attachments=[dict(
                fallback='Required plain-text summary of the attachment.',
                color={
                    'success': '#36a64f', 'warning': '#ff9966',
                    'error': '#cc3300'
                }[mode_type],
                pretext=event, author_name=mode,
                title='Open Application', title_link=link, text=event,
                fields=[dict(
                    type='mrkdwn',
                    value="*Application id:*\n%s" % self.reference_no
                ), dict(
                    type='mrkdwn',
                    value="*Advisor Name:*\n%s" % client.user.get_full_name()
                ), dict(
                    type='mrkdwn',
                    value="*Advisor phone:*\n%s" % client.user.account.phone_no
                )],
                thumb_url='https://onecover.in/favicon.png',
                footer='Post application flow',
                footer_icon='https://onecover.in/favicon.png',
                ts=now().timestamp()
            )]
        )
        return requests.post(endpoint, json=data)

    @property
    def adults(self):
        return self.active_members.filter(
            dob__year__lte=(now().year - 18)).count()

    @property
    def childrens(self):
        return self.active_members.count() - self.adults

    @cached_property
    def active_members(self):
        return self.member_set.filter(ignore=False)

    @cached_property
    def inactive_members(self):
        return self.member_set.exclude(ignore=False)

    @cached_property
    def company_category(self):
        return self.quote.premium.product_variant.company_category

    @cached_property
    def people_listed(self):
        return self.active_members.count()

    @cached_property
    def client(self):
        return self.app_client

    def __str__(self):
        return '%s - %s - %s' % (
            self.reference_no, self.application_type,
            self.company_category.company.name)

    class Meta:
        ordering = ('-created',)


class ExistingPolicies(BaseModel):
    application = models.ForeignKey(
        'sales.Application', on_delete=models.CASCADE, null=True, blank=True)
    insurer = models.CharField(max_length=128)
    suminsured = models.FloatField(default=0)
    deductible = models.FloatField(default=0)


class Member(BaseModel):
    application = models.ForeignKey(
        'sales.Application', on_delete=models.CASCADE)
    relation = models.CharField(
        max_length=128, choices=get_choices(Constants.RELATION_CHOICES),
        db_index=True)
    first_name = models.CharField(max_length=128, blank=True)
    last_name = models.CharField(max_length=128, blank=True)
    dob = models.DateField(null=True)
    gender = models.CharField(
        choices=get_choices(Constants.GENDER), max_length=16, null=True)
    occupation = models.CharField(
        choices=get_choices(Constants.OCCUPATION_CHOICES), max_length=32,
        null=True, blank=True)
    height = models.FloatField(default=0.0)
    weight = models.FloatField(default=0.0)
    ignore = models.BooleanField(default=None, db_index=True, null=True)

    def save(self, *ar, **kw):
        try:
            self.__class__.objects.get(pk=self.id)
        except self.__class__.DoesNotExist:
            if self.relation not in [
                'son', 'daughter'] and self.__class__.objects.filter(
                    relation=self.relation, application_id=self.application_id
            ).exists():
                raise IntegrityError(
                    '%s relation already exists.' % self.relation)
        super(Member, self).save(*ar, **kw)

    def update_fields(self, **kw):
        for field in kw.keys():
            setattr(self, field, kw[field])
        self.save()

    def get_full_name(self):
        name = '%s %s' % (self.first_name, self.last_name)
        return name.strip()

    @property
    def age(self):
        if self.dob:
            return int((
                now().today().date() - self.dob
            ).days / 365.2425)

    @property
    def height_foot(self):
        return int(self.height / 30.48)

    @property
    def height_inches(self):
        return round((self.height - self.height_foot * 30.48) / 2.54, 2)

    def __str__(self):
        return '%s | %s' % (self.relation.title(), self.application.__str__())


class Nominee(BaseModel):
    application = models.ForeignKey(
        'sales.Application', on_delete=models.CASCADE)
    relation = models.CharField(
        max_length=128, choices=get_choices(Constants.RELATION_CHOICES),
        db_index=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    phone_no = models.CharField(max_length=10)
    ignore = models.BooleanField(default=False)

    def save(self, *ar, **kw):
        if not self.__class__.objects.filter(pk=self.id):
            existing_nominee = self.__class__.objects.filter(
                application_id=self.application.id)
            if existing_nominee.exists():
                existing_nominee.update(ignore=True)
        super(Nominee, self).save(*ar, **kw)

    def get_full_name(self):
        name = '%s %s' % (
            self.first_name, self.last_name)
        return name.strip()


class Insurance(BaseModel):

    class Meta:
        abstract = True

    application = models.OneToOneField(
        'sales.Application', on_delete=models.CASCADE, null=True)


class HealthInsurance(Insurance):
    gastrointestinal_disease = JSONField(
        default=list, help_text=Constants.GASTROINTESTINAL_DISEASE)
    neuronal_diseases = JSONField(
        default=list, help_text=Constants.NEURONAL_DISEASES)
    oncology_disease = JSONField(
        default=list, help_text=Constants.ONCOLOGY_DISEASE)
    respiratory_diseases = JSONField(
        default=list, help_text=Constants.RESPIRATORY_DISEASES)
    cardiovascular_disease = JSONField(
        default=list, help_text=Constants.CARDIOVASCULAR_DISEASE)
    ent_diseases = JSONField(
        default=list, help_text=Constants.ENT_DISEASE)
    blood_diseases = JSONField(
        default=list, help_text=Constants.BLOOD_DISODER)
    alcohol_consumption = models.IntegerField(
        default=0.0, help_text=Constants.ALCOHOL_CONSUMPTION,
        null=True, blank=True)
    tobacco_consumption = models.IntegerField(
        default=0.0, help_text=Constants.TABBACO_CONSUMPTION,
        null=True, blank=True)
    cigarette_consumption = models.IntegerField(
        default=0.0, help_text=Constants.CIGARETTE_CONSUMPTION,
        null=True, blank=True)
    previous_claim = models.BooleanField(
        default=False, help_text=Constants.PREVIOUS_CLAIM,
        null=True, blank=True)
    proposal_terms = models.BooleanField(
        default=False, help_text=Constants.PROPOSAL_TERMS,
        null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    def update_default_fields(self, kw):
        for field in Constants.HEALTHINSURANCE_FIELDS:
            setattr(self, field, kw)
        self.save()

    def switch_premium(self, adults, childrens):
        opportunity = self.application.quote.opportunity
        data = dict(
            effective_age=(
                now().year - self.application.active_members.aggregate(
                    s=models.Min('dob'))['s'].year), adults=adults,
            product_variant_id=self.application.quote.premium.product_variant_id, # noqa
            childrens=childrens)
        for member in Constants.RELATION_CHOICES:
            members = self.application.active_members.filter(relation=member)
            if members.exists() and member not in ['son', 'daughter']:
                data['%s_age' % (member)] = members.get().age
        data['customer_segment_id'] = opportunity.category_opportunity.get_customer_segment(**data).id # noqa
        opportunity.refresh_quote_data(**data)
        quote = opportunity.get_quotes().first()
        if not quote:
            raise RecommendationException('No quote found for this creteria')
        previous_quote = self.application.quote
        if quote.id != previous_quote.id:
            previous_quote.status = 'rejected'
            previous_quote.save()
        quote.status = 'accepted'
        quote.save()
        self.application.quote_id = quote.id
        self.application.premium = quote.premium.amount
        self.application.suminsured = quote.premium.sum_insured
        self.application.save()

    def get_summary(self):
        response = dict()
        for field in self._meta.fields:
            if field.name in Constants.INSURANCE_EXCLUDE_FIELDS:
                continue
            field_value = getattr(self, field.name)
            if isinstance(field_value, list):
                values = list()
                for row in field_value:
                    if row['value']:
                        values.append(
                            Member.objects.get(id=row['id']).relation)
                field_value = None
                if values:
                    field_value = ", ".join(values)
            if not field_value:
                continue
            response[field.name] = field_value
        return response

    def get_insurance_fields(self):
        field_data = list()
        from sales.serializers import (
            MemberSerializer, GetInsuranceFieldsSerializer)
        members = self.application.active_members or Member.objects.filter(
            application_id=self.application_id)
        for field in self._meta.fields:
            if field.name in Constants.INSURANCE_EXCLUDE_FIELDS:
                continue
            if field.__class__.__name__ not in [
                    'BooleanField', 'IntegerField']:
                members_data = list()
                for member in getattr(self, field.name):
                    row = MemberSerializer(
                        members.get(id=member['id'])).data
                    row['value'] = member['value']
                    members_data.append(row)
            if field.__class__.__name__ == 'BooleanField':
                data = dict(
                    text=field.help_text, field_name=field.name,
                    field_requirements=[{
                        'relation': 'None',
                        'value': getattr(self, field.name)
                    }])
            elif field.__class__.__name__ == 'IntegerField':
                data = dict(
                    text=field.help_text, field_name=field.name,
                    field_requirements=[{
                        'relation': 'None',
                        'consumption': getattr(self, field.name)
                    }])
            else:
                data = dict(
                    text=field.help_text, field_name=field.name,
                    field_requirements=members_data)
            serializer = GetInsuranceFieldsSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            field_data.append(serializer.data)
        return field_data


class TravelInsurance(Insurance):
    name = models.CharField(max_length=32)


class ProposerDocument(BaseModel):
    contact = models.ForeignKey('crm.Contact', on_delete=models.CASCADE)
    document_number = models.CharField(max_length=64, null=True, blank=True)
    document_type = models.CharField(
        choices=get_choices(Constants.KYC_DOC_TYPES), max_length=16)
    file = models.FileField(
        upload_to=get_proposer_upload_path, null=True, blank=True)
    ignore = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        previous = self.__class__.objects.filter(
            document_type=self.document_type, contact_id=self.contact_id)
        if previous.exists():
            previous.update(ignore=True)
        super(self.__class__, self).save(*args, **kwargs)


class Policy(BaseModel):
    application = models.OneToOneField(
        'sales.Application', on_delete=models.CASCADE)
    policy_number = models.CharField(max_length=64, blank=True, null=True)
    policy_data = JSONField(default=dict)
    policy_file = models.FileField(
        upload_to=Constants.POLICY_UPLOAD_PATH,
        null=True, blank=True)


@receiver(post_save, sender=Application, dispatch_uid="action%s" % str(now()))
def application_post_save(sender, instance, created, **kwargs):
    if created:
        Quote.objects.filter(
            opportunity_id=instance.quote.opportunity_id).exclude(
                id=instance.quote_id, status__in=['accepted', 'rejected']
        ).update(status='rejected')
        quote = instance.quote
        quote.status = 'accepted'
        quote.save()
        # do this thing async
        instance.add_default_members()
        ContentType.objects.get(
            model=instance.application_type, app_label='sales'
        ).model_class().objects.create(application_id=instance.id)
        from sales.tasks import update_insurance_fields
        update_insurance_fields(instance.id)
    instance.invalidate_cache()
