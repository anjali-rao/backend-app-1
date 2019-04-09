# Choices
GENDER = ('male', 'female', 'transgender')
USER_TYPE = ('enterprise', 'subscriber', 'pos')
CITY_TIER = ((0, 'First'), (1, 'Second'), (2, 'Third'))
USER_FLAG = {'blacklist': False, 'training': False, 'exam_passed': None}
OCCUPATION_CHOICES = (
    (0, 'Student'), (1, 'Service'), (3, 'Self Employeed'), (4, 'Other'))
LEAD_STATUS_CHOICES = (
    (0, 'Fresh'), (1, 'In Progress'), (2, 'Closed'), (3, 'Dropped'))
LEAD_STAGE_CHOICES = (
    (0, 'New'), (1, 'Appointment Scheduled'), (2, 'Needs'), (3, 'Quote'),
    (4, 'Cart'), (5, 'Proposal'), (6, 'Payment'), (7, 'Submitted'),
    (8, 'Issued'))
STATUS_CHOICES = (('pending','Pending'),('accepted','Accepted'),('rejected','Rejected')) # noqa
KYC_DOC_TYPES = ('pan', 'passport', 'voter_card')
QUESTION_COICES = ('mcq', 'single')
HELP_FILES_TYPE = ('ALL', 'SALES BROCHURES', 'CLAIM FORMS')
CONTACT_CHANNELS = ('phone', 'email', 'whatsapp')
FEATURE_TYPES = (
    'Must Have', 'Others', 'Good to Have', 'Addons & Discounts', 'Value-add',
    'Exclusion')
APPLICATION_TYPES = ('health_insurance')

DOC_TYPES = ('pan', 'license', 'photo')
DOCS_UPLOAD_TYPES = {
    'pan': 'advisor/pan',
    'license': 'advisor/license',
    'photo': 'advisor/selfie'
}
TIER_1_CITIES = ('Bengaluru', 'Delhi', 'Mumbai', 'Kolkota')
TIER_2_CITIES = ('Lucknow', 'Allahabad')

API_CACHE_TIME = 3600

# Defaults
DEFAULT_LOGO = 'enterprise/goplannr.jpeg'
HELP_FILES_PATH = 'contents'
DEFAULT_HEXA_CODE = '#005db1'
OCCUPATION_DEFAULT_CHOICE = 3
DEFAULT_USER_TYPE = 'subscriber'
DEFAULT_ENTERPRISE = 'GoPlannr'
DEFAULT_BASE_PREMIUM = 0.0
DEFAULT_GST = 0.18
DEFAULT_COMMISSION = 0.20
ADULT_AGE_LIMIT = 18

# Success messages
OTP_MESSAGE = 'Your One Time Password for GoPlannr is : %s'
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
USER_ALREADY_EXISTS = 'User already exists for choosen product.'

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
