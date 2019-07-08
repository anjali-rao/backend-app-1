import csv

from django.db import transaction
from django.http import HttpResponse


def export_as_csv(self, request, queryset):
    meta = self.model._meta
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename={}.csv'.format(meta)
    writer = csv.writer(response)

    fk_fields = []
    if hasattr(self, 'fk_fields'):
        fk_fields = [f.split('__') for f in self.fk_fields]
    primary_field_names = [
        field.name for field in meta.fields if [field.name] not in fk_fields
    ]
    header = False

    for obj in queryset:
        nested_fields = []
        row = [
            getattr(obj, field) for field in primary_field_names
            if [field] not in fk_fields
        ]
        for field_list in fk_fields:
            fk_obj = obj
            for field in field_list:
                fk_obj = getattr(fk_obj, field)
                fk_dict = fk_obj.__dict__
                nested_fields.extend(
                        ["__".join(field_list) + "_"
                            + key for key in fk_dict.keys()
                            if key != '_state']
                )
                row.extend(
                    [val for key, val in fk_dict.items() if key != '_state']
                )
        if not header:
            writer.writerow(primary_field_names + nested_fields)
            header = True

        writer.writerow(row)
    return response


export_as_csv.short_description = "Export Selected as CSV"


def readcsv(filename):
    data = list()
    with open(filename) as tsvfile:
        tsvreader = csv.DictReader(tsvfile, delimiter=",")
        for line in tsvreader:
            data.append(line)
        tsvfile.close()
    return data


def create_csv(data, file_name=None):
    """
    Use create_csv method instead of this.
    Accepts list of dictionaries and save them as csvfile
    Created for upload type dashboards
    """
    import csv
    filepath = file_name
    keys = sorted(data[0].keys())
    with open(filepath, 'w') as csvfile:
        dict_writer = csv.DictWriter(csvfile, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    return filepath


def update_pincode(filename):
    from users.models import Pincode, State
    data = readcsv(filename)
    for row in data:
        pincode, created = Pincode.objects.get_or_create(
            pincode=row['pincode'])
        pincode.city = row['taluk']
        if pincode.city.lower() == 'na':
            pincode.city = row['regionname']
        state, created = State.objects.get_or_create(
            name=row['statename'].title())
        pincode.state_id = state.id
        pincode.save()


def upload_suminsurred(filename):
    from product.models import SumInsuredMaster
    data = readcsv(filename)
    for row in data:
        amount = int(row[' number '].replace(',', '').replace(',', ''))
        instance, created = SumInsuredMaster.objects.get_or_create(
            number=amount)
        if created:
            instance.text = row['text']
            instance.save()


def upload_company(filename):
    with transaction.atomic():
        from product.models import Company, Category
        data = readcsv(filename)
        for row in data:
            category = Category.objects.get(name=row['category'].replace('{','').replace('}','').title()) # noqa
            instance, created = Company.objects.get_or_create(pk=row['id'])
            instance.name = row['company_name']
            instance.categories.add(category.id)
            instance.short_name = row['company_shortname']
            instance.website = row['website']
            instance.spoc = row['spoc']
            instance.website = row['website']
            instance.toll_free_number = row['tollfree'].split(',')
            instance.long_description = row['long description']
            instance.small_description = row['short description']
            instance.commission = float(row['commission'] or 0.0)
            instance.save()


def upload_companycategory(filename):
    from product.models import Company, CompanyCategory
    with transaction.atomic():
        for row in readcsv(filename):
            company = Company.objects.get(short_name=row['company name'])
            instance, created = CompanyCategory.objects.get_or_create(
                company_id=company.id, category_id=row['category_id'])
            instance.company_id = company.id
            instance.category_id = row['category_id']
            instance.claim_settlement = row['claim_settlement']
            instance.save()


def upload_customersegment():
    from product.models import CustomerSegment
    for segement in [
        'chronic', 'self_employed', 'active', 'young_adult',
        'young_adult_with_dependent_parents', 'young_couple', 'young_family',
            'middle_aged_family', 'senior_citizens']:
        CustomerSegment.objects.get_or_create(name=segement)


def upload_feature_master(filename):
    from product.models import FeatureMaster
    for row in readcsv(filename):
        instance, created = FeatureMaster.objects.get_or_create(pk=row['id'])
        instance.category_id = 1
        instance.name = row['feature_name']
        instance.feature_type = row['feature_type']
        instance.short_description = row['short_description']
        instance.long_description = row['long_description']
        instance.save()


def upload_product_variant(filename):
    with transaction.atomic():
        from product.models import ProductVariant
        for row in readcsv(filename):
            instance, created = ProductVariant.objects.get_or_create(
                pk=row['id'])
            instance.company_category_id = row['companycategory id']
            instance.name = row['product name']
            instance.feature_variant = row['variant feature']
            instance.short_description = row['short description']
            instance.long_description = row['long description']
            if instance.id != int(row['parent product']):
                instance.parent_id = row['parent product']
            instance.chronic = False
            instance.save()


def upload_feature(filename):
    from product.models import Feature
    for row in readcsv(filename):
        instance, created = Feature.objects.get_or_create(pk=row['id'])
        instance.product_variant_id = row['productvariant_id']
        instance.feature_master_id = row['feature_master_id']
        instance.rating = float(row['rating'] or 0)
        instance.short_description = row['short_description']
        instance.long_description = row['long_description']
        instance.save()


def upload_premiums(filename):
    with transaction.atomic():
        from product.models import HealthPremium as Premium
        from psycopg2.extras import NumericRange
        import re
        for row in readcsv(filename):
            suminsured = int(float(re.sub('[ ,]', '', row['sum_insured'])))
            min_suminsured = int(float(re.sub('[ ,]', '', row['min_sum_insured'])))
            instance, created = Premium.objects.get_or_create(pk=row['id'])
            instance.sum_insured = suminsured
            instance.base_premium = re.sub('[ ,]', '', row['base_premium'])
            instance.age_range = NumericRange(
                lower=int(row['min_age']), upper=int(row['max_age']) + 1)
            instance.suminsured_range = NumericRange(
                lower=min_suminsured, upper=suminsured + 1)
            instance.adults = int(row['adults'])
            instance.childrens = int(row['children'])
            instance.citytier = row['variant_city_tier']
            instance.product_variant_id = row['productvariant_id']
            instance.gst = float(int(row['gst'].replace('%', ''))) / 100
            instance.commission = float(
                int(row['commission'].replace('%', ''))) / 100
            instance.save()


def upload_customersegmentfeaturescore(filename):
    from product.models import (
        FeatureMaster, FeatureCustomerSegmentScore, CustomerSegment
    )
    for row in readcsv(filename):
        feature_masters = FeatureMaster.objects.filter(
            name=row['Feature_master'])
        feature_types = [i for i, j in row.items() if i != 'Feature_master' and i != 'Base'] # noqa
        if not feature_masters.exists():
            continue
        feature_master = feature_masters.get()
        for feature in feature_types:
            score = row[feature].replace('%', '')
            if score == '':
                continue
            customer_segment = CustomerSegment.objects.get(
                name=feature.replace('-', '_').replace(' ', '_'))
            instance = FeatureCustomerSegmentScore.objects.get_or_create(
                feature_master_id=feature_master.id,
                customer_segment_id=customer_segment.id)[0]
            instance.score = float(score) / 100
            instance.save()

