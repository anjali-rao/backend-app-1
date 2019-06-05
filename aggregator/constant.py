# MAPPING ==============================================

RELATION_CODE = dict(
    self='R001', spouse='R002', mother='R005', father='R006', son='R003',
    daughter='R004', brother='R009', sister='R010', cousin='R009'
)

OCCUPATION_CODE = dict(
    self_employed_or_business='O003', salaried='O002', retired='O005',
    unemployed='O009', others='O009'
)

STATE_CODE = {
    'Andaman & Nicobar Islands': '001', 'Andhra Pradesh': '002',
    'Arunachal Pradesh': '003', 'Assam': '004', 'Bihar': '005',
    'Chandigarh': '006', 'Chattisgarh': '007', 'Dadra & Nagar Haveli': '008',
    'Daman & Diu': '009', 'Delhi': '010', 'Goa': '011', 'Gujarat': '012',
    'Haryana': '013', 'Himachal Pradesh': '014', 'Jammu & Kashmir': '015',
    'Jharkhand': '016', 'Karnataka': '017', 'Kerala': '018',
    'Lakshadweep': '019', 'Madhya Pradesh': '020', 'Maharashtra': '021',
    'Manipur': '022', 'Meghalaya': '023', 'Mizoram': '024', 'Nagaland': '025',
    'Odisha': '026', 'Pondicherry': '027', 'Punjab': '028', 'Rajasthan': '029',
    'Sikkim': '030', 'Tamil Nadu': '031', 'Telangana': '036', 'Tripura': '032',
    'Uttar Pradesh': '033', 'Uttarakhand': '034', 'West Bengal': '035'
}

GENDER = dict(male='M', female='F')

SECTION = dict(healthinsurance='mediclaim')

COMPANY_NAME = {
    'Aditya Birla Health Insurance': 'Aditya Birla Health Insurance',
    'HDFC ERGO General Insurance': 'HDFC ERGO General Insurance Co. Ltd.'
}

INCOME = {
    '< 3 Lakhs': 300000, '3 - 5 lakhs': 500000, '5 - 10 lakhs': 1000000,
    '10 - 20 lakhs': 2000000, '> 20 lakhs': 5000000
}


# CONSTANTS ==============================================

WALLNUT_SI = [
    '150000', '200000', '300000', '400000', '500000', '700000', '750000',
    '1000000', '1500000', '2000000', '2500000', '3000000', '3500000',
    '4000000', '4500000', '5000000']


# METHODS ==============================================

def get_marital_status(relation):
    if relation in ['son', 'daughter']:
        return 'Single'
    elif relation in 'self':
        return None
    return 'Married'


# COMMUNICATIONS  ==============================================

PAYMENT_MESSAGE = 'Hi %s. Thankyou for choosing OneCover.\nYour application(# %s) has been submitted successfully.\nYour payment of Rs.%s is due against your %s plan.\nClick on the link to pay now\n%s\n\nRegards\nTeam OneCover' # noqa

# ENDPOINTS  ==============================================

ADITYA_BIRLA_HEALTH_INSURANCE_STATE_CITY_API = 'health/proposal_aditya_birla/get_state_city?Pincode=%s' # noqa
HDFC_ERGO_GENERAL_INSURANCE_STATE_CITY_API = ''
BAJAJ_ALLIANZ_GIC = 'health/proposal_bajaj_allianz/get_state_and_city_from_pincode' # noqa

ADITYA_BIRAL_PROPOSAL_URL = 'health/proposal_aditya_birla/save_proposal_data'
ADITYA_BIRAL_PROPOSAL_SUBMIT_URL = 'health/proposal_aditya_birla/proposal_submit' # noqa
ADITYA_BIRLA_CHECK_PROPOSAL_DATE_URL = 'check_proposal_date'

HDFC_ERGO_PROPOSAL_URL = 'health/proposal_hdfc_ergo/save_proposer_data'
HDFC_ERGO_CHECK_PROPOSAL_DATE_URL = 'check_proposal_date'

BAJAJ_ALLIANZ_GIC_PROPOSAL_URL = 'health/proposal_bajaj_allianz/save_proposal'
BAJAJ_ALLIANZ_GIC_CHECK_PROPOSAL_DATE_URL = 'check_proposal_date'
