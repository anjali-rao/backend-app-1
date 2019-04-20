# Choices
GENDER = ('male', 'female', 'transgender')

USER_TYPE = ('enterprise', 'subscriber', 'pos')

CITY_TIER = ((0, 'First'), (1, 'Second'), (2, 'Third'))

USER_FLAG = {'blacklist': False, 'training': False, 'exam_passed': None}

OCCUPATION_CHOICES = ('student', 'service', 'self_employeed', 'others')

LEAD_STATUS_CHOICES = (
    ('fresh', 'Fresh'), ('inprogress', 'In Progress'),
    ('closed', 'Closed'), ('dropped', 'Dropped'))

LEAD_STAGE_CHOICES = (
    ('new', 'New'), ('appointment_scheduled', 'Appointment Scheduled'),
    ('needs', 'Needs'), ('quote', 'Quote'), ('cart', 'Cart'),
    ('proposal', 'Proposal'), ('payment', 'Payment'),
    ('submitted', 'Submitted'), ('issued', 'Issued'))

STATUS_CHOICES = (('pending','Pending'),('accepted','Accepted'),('rejected','Rejected')) # noqa
KYC_DOC_TYPES = ('pan', 'passport', 'voter_card')
QUESTION_COICES = ('mcq', 'single')
HELP_FILES_TYPE = ('ALL', 'SALES BROCHURES', 'CLAIM FORMS')
CONTACT_CHANNELS = ('phone', 'email', 'whatsapp')
RELATION_CHOICES = (
    'self', 'spouse', 'mother', 'father', 'son', 'daughter', 'brother', 'sister'
)

FEATURE_TYPES = (
    'Must Have', 'Others', 'Good to Have', 'Addons & Discounts', 'Value-add',
    'Exclusion')

APPLICATION_TYPES = ('health_insurance', 'travel_insurance')

DOC_TYPES = ('pan', 'license', 'photo')

DOCS_UPLOAD_TYPES = {
    'pan': 'advisor/pan',
    'license': 'advisor/license',
    'photo': 'advisor/selfie'
}

TIER_1_CITIES = ('Bengaluru', 'Delhi', 'Mumbai', 'Kolkota')
TIER_2_CITIES = ('Lucknow', 'Allahabad')

EARNING_TYPES = ('commission', 'incentive')

MARITAL_STATUS = ('married', 'single', 'divorced')

# Defaults
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

# Success messages
OTP_MESSAGE = '<#> Your One Time Password for OneCover is %s XTmeqjNJd+R'
OTP_SUCCESS = 'OTP verified successfully.'
OTP_GENERATED = 'OTP send successfully.'
AUTHORIZATION_GENERATED = 'Authorization key generated successfully.'
PASSWORD_CHANGED = 'Password changed successfully.'
USER_CREATION_MESSAGE = 'Hi,\nYour account with GoPlannr has been created successfully with phone no %s.\n\nRegards\nTeam GoPlannr' # noqa
USER_CREATED_SUCESS = 'User created successfully!'
USER_PASSWORD_CHANGE = 'Hi,\nYour GoPlannr account password has been changed successfully.\n\nRegards\nTeam GoPlannr' # noqa

# TTL's (seconds)
OTP_TTL = 900
TRANSACTION_TTL = 900

POST_REQUEST_ONLY = ['put', 'delete']

# Exception messages
REFERRAL_CODE_EXCEPTION = 'Invalid referral code provided.'
OTP_VALIDATION_FAILED = 'Invalid otp provided.'
INVALID_TRANSACTION_ID = 'Invalid transaction id provided.'
INVALID_PHONE_NO = 'Invalid phone no entered.'
INVALID_USERNAME = 'Invalid username provided.'
INVALID_PASSWORD = 'Invalid password provided.'
INVALID_USERNAME_PHONE_COMBINATION = 'Invalid username and phone no combination.' # noqa
PASSWORD_MISMATCH = 'Password and confirm password mismatch'
ACCOUNT_DISABLED = 'Account is unactive. Please contact Goplannr for reactivation' # noqa
INVALID_CATEGORY_ID = 'Category id passed is invalid or category doesnot exists.' # noqa
INVALID_CUSTOMER_SEGMENT = 'Invalid Customer Segment id'
INVALID_ANSWER_ID = 'Invalid Answer id provided.'
INVALID_QUESTION_ID = 'Invalid Answer id provided.'
INVALID_GENDER_PROVIDED = 'Invalid gender input provided.'
INVALID_PINCODE = 'Invalid pincode provided.'
USER_ALREADY_EXISTS = 'User already exists as subscriber.'
FAILED_APPLICATION_CREATION = 'Failed to add contact. Please contact GoPlannr.'
APPLICATION_ALREAY_EXISTS = 'Application already exists with quote id.'

# Creation Fields
ACCOUNT_CREATION_FIELDS = (
    'password', 'first_name', 'last_name', 'email',
    'pincode_id', 'pan_no'
)


# Upload paths
COMPANY_UPLOAD_PATH = 'company'
ENTERPRISE_UPLOAD_PATH = 'enterprise'
CATEGORY_UPLOAD_PATH = 'category'

DEBUG_HOST = 'http://localhost:8000'

GASTROINTESTINAL_DISEASE = 'Disease of Kidney, Digestive tract, Liver/Gall Bladder, Pancreas, Breast, Reproductive /Urinary system, or any past complications of pregnancy/ child birth including high blood pressure or diabetes etc' # noqa
NEURONAL_DISEASES = 'Disease of the Brain/Spine/Nervous System, Epilepsy, Paralysis, Polio, Joints/Arthritis, Congenital/ Birth defect, Physical deformity/disability, HIV/AIDS, other Sexually Transmitted Disease or Accidental injury or any other medical (other than common cold & viral fever) or surgical condition or Investigation parameter has been detected to be out of range/ not normal?' # noqa
ALCOHOL_CONSUMPTION = 'Does any person proposed to be insured consume alcohol?' # noqa
TABBACO_CONSUMPTION = 'Does any person proposed to be insured consume Pan Masala/Gutka ?' # noqa
CIGARETTE_CONSUMPTION = 'Does any person proposed to be insured smoke?' # noqa
PREVIOUS_CLAIM = 'Claim in previous policy.' # noqa
PROPOSAL_TERMS = 'Was any proposal for life, health, hospital daily cash or critical illness insurance declined, deferred, withdrawn or accepted with modified terms' # noqa
EXISTING_POLICY = 'Do you have Previous/ Current policy for life, health, hospital daily cash or critical illness insurance?' # noqa
ONCOLOGY_DISEASE = 'Cancer, Tumour, lump, cyst, ulcer'
ENT_DISEASE = 'Disease of Eye, Ear, Nose, Throat, Thyroid'
CARDIOVASCULAR_DISEASE = 'Tuberculosis (TB), any Respiratory / Lung disease' 
RESPIRATORY_DISEASES = 'Any form of Heart Disease, Peripheral Vascular Disease, procedures like Angioplasty/PTCA/By Pass Surgery, valve replacement etc' 
BLOOD_DISODER = 'Diabetes, High blood pressure, High Cholesterol, Anaemia / Blood disorder (whether treated or not)'
