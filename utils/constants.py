# Choices  ==================================

GENDER = ('male', 'female', 'transgender')
USER_TYPE = ('enterprise', 'subscriber', 'pos')
OCCUPATION_CHOICES = (
    'self_employed_or_business', 'salaried', 'retired', 'unemployed', 'others')
LEAD_STATUS_CHOICES = (
    ('fresh', 'Fresh'), ('inprogress', 'In Progress'),
    ('closed', 'Closed'), ('dropped', 'Dropped'))
LEAD_STAGE_CHOICES = (
    ('new', 'New'), ('appointment_scheduled', 'Appointment Scheduled'),
    ('needs', 'Needs'), ('quote', 'Quote'), ('cart', 'Cart'),
    ('proposal', 'Proposal'), ('payment', 'Payment'),
    ('submitted', 'Submitted'), ('issued', 'Issued'))
STATUS_CHOICES = (
    ('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'),
    ('completed', 'Completed'))
APPLICATION_STATUS = (
    ('fresh', 'Fresh'), ('pending', 'Pending'), ('submitted', 'Submitted'),
    ('approved', 'Approved'), ('cancelled', 'Cancelled'),
    ('completed', 'Completed'))
APPLICATION_STAGES = (
    'proposer_details', 'insured_members', 'nominee_details',
    'health_details', 'summary', 'completed')
KYC_DOC_TYPES = (
    'pancard', 'aadhaar_card', 'driving_license', 'bank_passbook',
    'ration_card', 'passport', 'birth_certificate', 'cancelled_cheque',
    'photo')
QUESTION_COICES = ('mcq', 'single')
HELP_FILES_TYPE = ('all', 'sales_brochure', 'claim_form')
CONTACT_CHANNELS = ('phone', 'email', 'whatsapp')
RELATION_CHOICES = (
    'self', 'spouse', 'mother', 'father', 'son', 'daughter', 'brother',
    'sister', 'cousin')
DOC_TYPES = ('pan', 'license', 'photo')
DOCS_UPLOAD_TYPES = dict(
    pan='advisor/pan', license='advisor/license', photo='advisor/selfie')
FEATURE_TYPES = (
    'Must Have', 'Others', 'Good to Have', 'Addons & Discounts', 'Value-add',
    'Exclusion')
APPLICATION_TYPES = ('healthinsurance', 'travelinsurance')
TIER_1_CITIES = ('Bengaluru', 'Delhi', 'Mumbai', 'Kolkota')
TIER_2_CITIES = ('Lucknow', 'Allahabad')
EARNING_TYPES = ('commission', 'incentive', 'referral')
MARITAL_STATUS = ('married', 'single', 'divorced')
PLAYLIST_CHOICES = ('marketing', 'training')
USER_FILE_UPLOAD = ['cancelled_cheque', 'photo']
REQUEST_CHOICES = ['GET', 'POST', 'PUT', 'PATCH']
AGGREGATOR_CHOICES = ['offline', 'wallnut']
EARNING_STATUS = ('paid', 'pending', 'processing')
ACTIVE_AGGREGATOR_COMPANIES = [
    'Aditya Birla Health Insurance', 'HDFC ERGO General Insurance']


# ORDERS  ==================================

MEMBER_ORDER = {key: i for i, key in enumerate(['self', 'spouse', 'father', 'mother'])} # noqa
CATEGORY_ORDER = {key: i for i, key in enumerate(['Health', 'Travel'])} # noqa


# ROUGH HANDLING  ==================================

MUMBAI_NCR_TIER = ['Mumbai & NCR', 'All India']
MUMBAI_AREA_TIER = ['Mumabi', 'Navi Mumbai']
ALL_INDIA_TIER = CITY_TIER = ['All India', 'All India except Mumbai & NCR']
NCR_PINCODES = [
    110001, 110002, 110003, 110004, 110005, 110006, 110007, 110008, 110009,
    110010, 110011, 110012, 110013, 110014, 110015, 110016, 110017, 110018,
    110019, 110020, 110021, 110022, 110023, 110024, 110025, 110026, 110027,
    110028, 110029, 110030, 110031, 110032, 110033, 110034, 110035, 110036,
    110037, 110038, 110039, 110040, 110041, 110042, 110043, 110044, 110045,
    110046, 110047, 110048, 110049, 110051, 110052, 110053, 110054, 110055,
    110056, 110057, 110058, 110059, 110060, 110061, 110062, 110063, 110064,
    110065, 110066, 110067, 110068, 110070, 110071, 110073, 110074, 110075,
    110076, 110078, 110081, 110082, 110083, 110084, 110085, 110086, 110087,
    110088, 110091, 110092, 110093, 110094, 110095, 110096, 201301, 122001,
    201001, 201009, 121001, 121002, 124507
]
USER_FLAG = dict(blacklist=False, training=False, exam_passed=False)
HEALTHINSURANCE_FIELDS = [
    'gastrointestinal_disease', 'neuronal_diseases', 'oncology_disease',
    'respiratory_diseases', 'cardiovascular_disease', 'ent_diseases',
    'blood_diseases'
]
INSURANCE_EXCLUDE_FIELDS = ['id', 'created', 'modified', 'application']


# Defaults ==================================

DEFAULT_LOGO = 'enterprise/goplannr.jpeg'
HELP_FILES_PATH = 'contents'
DEFAULT_HEXA_CODE = '#005db1'
OCCUPATION_DEFAULT_CHOICE = 'others'
DEFAULT_USER_TYPE = 'subscriber'
DEFAULT_ENTERPRISE = 'GoPlannr'
DEFAULT_BASE_PREMIUM = 0.0
DEFAULT_GST = 0.18
DEFAULT_COMMISSION = 0.20
ADULT_AGE_LIMIT = 18
API_CACHE_TIME = 3600

# Success messages  ==================================
OTP_MESSAGE = '<#> Your One Time Password for OneCover is %s XTmeqjNJd+R'
OTP_SUCCESS = 'OTP verified successfully.'
OTP_GENERATED = 'OTP send successfully.'
AUTHORIZATION_GENERATED = 'Authorization key generated successfully.'
PASSWORD_CHANGED = 'Password changed successfully.'
USER_CREATION_MESSAGE = 'Hi,\nYour account with OneCover has been created successfully with phone no %s.\n\nRegards\nTeam OneCover' # noqa
USER_CREATED_SUCESS = 'User created successfully!'
USER_PASSWORD_CHANGE = 'Hi,\nYour OneCover account password has been changed successfully.\n\nRegards\nTeam OneCover' # noqa
PASSWORD_REQUIRED = 'Password is required.'
PROMO_MESSAGE = 'Hi %s, Welcome to OneCover, download our app and become super advisor https://tinyurl.com/y2ux5cdj .' # noqa
PAYMENT_LINK_GENERATION = 'Payment link generated successfully for application (%s). ' # noqa
SEND_TO_AGGREGATOR = 'Application (%s) successfully send to aggregator.'


# TTL's (seconds)  ==================================

OTP_TTL = 900
TRANSACTION_TTL = 900


# Exception messages  ==================================

REFERRAL_CODE_EXCEPTION = 'Invalid referral code provided.'
OTP_VALIDATION_FAILED = 'Invalid otp provided.'
INVALID_TRANSACTION_ID = 'Invalid transaction id provided.'
INVALID_PHONE_NO = 'Invalid phone no entered.'
INVALID_USERNAME = 'Invalid username provided.'
INVALID_PASSWORD = 'Invalid password provided.'
INVALID_USERNAME_PHONE_COMBINATION = 'Invalid username and phone no combination.' # noqa
PASSWORD_MISMATCH = 'Password and confirm password mismatch'
ACCOUNT_DISABLED = 'Account is unactive. Please contact OneCover for reactivation' # noqa
INVALID_CATEGORY_ID = 'Category id passed is invalid or category doesnot exists.' # noqa
INVALID_CUSTOMER_SEGMENT = 'Invalid Customer Segment id'
INVALID_ANSWER_ID = 'Answer id: %s is invalid.'
INVALID_QUESTION_ID = 'Question id: %s is invalid.'
INVALID_GENDER_PROVIDED = 'Invalid gender input provided.'
INVALID_PINCODE = 'Invalid pincode provided.'
USER_ALREADY_EXISTS = 'User already exists with provided input.'
FAILED_APPLICATION_CREATION = 'Failed to add contact. Please contact OneCover.'
APPLICATION_ALREAY_EXISTS = 'Application already exists with quote id.'
ANSWER_CANNOT_BE_LEFT_BLANK = 'Answers are required.'
INVALID_FAMILY_DETAILS = 'Please provide valid family details.'
LEAD_ERROR = 'Lead not provided or invalid lead id provided.'
NO_QUOTES_FOUND = 'No Quotes found for given suminsured.'
INVALID_INPUT = 'Invalid input provided.'
COMPARISION_ERROR = 'Atleast two quotes are required for comparision'
INCOMPLETE_APPLICATION = 'Application not completed, please fill %s'
LOOKUP_ERROR = 'Expected view %s to be called with a URL keyword argument '
'named "%s". Fix your URL conf, or set the `.lookup_field` '
'attribute on the view correctly.'
APPLICATION_UNMAPPED = 'Application not mapped to any insurance or inproper application type' # noqa
INVALID_QUOTE_ID = 'Invalid Quote id provided.'
INVALID_QUESTION_ANSWER_COMBINATION = 'Invalid question and answer combination provided'  # noqa
INVALID_LEAD_ID = 'Invalid / missing Lead id.'
INVALID_PHONE_NO_FORMAT = 'Phone number is not valid'
INVALID_PLAYLIST_TYPE = 'Playlist type provided is invalid.'
PLAYLIST_UNAVAILABLE = 'No playlist available. Please Contact Admin.'
INVALID_CONTACT_ID = 'Invalid contact id provided.'
INVALID_LEAD_STAGE = 'Invalid lead stage'
PASSWORD_NOT_SET = 'Password is not set.'
PAYMENT_LINK_GENERATION_FAILED = 'Failed to generate payment link for application (%s), due to exception:%s' # noqa
FAILED_TO_SEND_TO_AGGREGATOR = 'Failed to send application (%s) to aggregator due to exception: %s' # noqa
CONTACT_DETAILS_REQUIRED = 'Contact name and Contact phone_no is required'
DUPLICATE_LEAD = 'Lead already exists with similar contact_name and contact_phone_no' # noqa


# Creation Fields  ==================================

ACCOUNT_CREATION_FIELDS = (
    'password', 'first_name', 'last_name', 'email',
    'address_id', 'pan_no', 'fcm_id'
)
ACCOUNT_UPDATION_FIELDS = (
    'first_name', 'last_name', 'email', 'address_id', 'pan_no')
ADDRESS_UPDATE_FIELDS = ['flat_no', 'street', 'landmark']
CONTACT_CREATION_FIELDS = (
    'first_name', 'last_name', 'phone_no', 'dob', 'annual_income',
    'occupation', 'marital_status', 'email')
GENERIC_LEAD_FIELDS = (
    'category_id', 'pincode', 'bookmark', 'user_id', 'ignore', 'contact_id')


# Upload paths  ==================================

COMPANY_UPLOAD_PATH = 'company'
ENTERPRISE_UPLOAD_PATH = 'enterprise'
CATEGORY_UPLOAD_PATH = 'category'
POLICY_UPLOAD_PATH = 'policy'
DEBUG_HOST = 'http://localhost:8000'


# Help- Texts  ==================================

GASTROINTESTINAL_DISEASE = 'Disease of Kidney, Digestive tract, Liver/Gall Bladder, Pancreas, Breast, Reproductive /Urinary system, or any past complications of pregnancy/ child birth including high blood pressure or diabetes etc' # noqa
NEURONAL_DISEASES = 'Disease of the Brain/Spine/Nervous System, Epilepsy, Paralysis, Polio, Joints/Arthritis, Congenital/ Birth defect, Physical deformity/disability, HIV/AIDS, other Sexually Transmitted Disease or Accidental injury or any other medical (other than common cold & viral fever) or surgical condition or Investigation parameter has been detected to be out of range/ not normal?' # noqa
ALCOHOL_CONSUMPTION = 'Does any person proposed to be insured consume alcohol ?' # noqa
TABBACO_CONSUMPTION = 'Does any person proposed to be insured consume Pan Masala/Gutka ?' # noqa
CIGARETTE_CONSUMPTION = 'Does any person proposed to be insured smoke?' # noqa
PREVIOUS_CLAIM = 'Claim in previous policy.' # noqa
PROPOSAL_TERMS = 'Was any proposal for life, health, hospital daily cash or critical illness insurance declined, deferred, withdrawn or accepted with modified terms ?' # noqa
EXISTING_POLICY = 'Do you have Previous/ Current policy for life, health, hospital daily cash or critical illness insurance?' # noqa
ONCOLOGY_DISEASE = 'Cancer, Tumour, lump, cyst, ulcer'
ENT_DISEASE = 'Disease of Eye, Ear, Nose, Throat, Thyroid'
CARDIOVASCULAR_DISEASE = 'Tuberculosis (TB), any Respiratory / Lung disease'
RESPIRATORY_DISEASES = 'Any form of Heart Disease, Peripheral Vascular Disease, procedures like Angioplasty/PTCA/By Pass Surgery, valve replacement etc' # noqa
BLOOD_DISODER = 'Diabetes, High blood pressure, High Cholesterol, Anaemia / Blood disorder (whether treated or not)' # noqa
COMMISSION_TEXT = 'Commission for policy # %s issued on %s to %s'
REFERRAL_TEXT = 'Referring to %s'
INCENTIVE_TEXT = 'Incentive for %s'


# Category Lead - Mapper  ==================================
CATEGORY_LEAD_FIELDS_MAPPER = dict(
    healthinsurance=['gender', 'family', 'effective_age']
)
