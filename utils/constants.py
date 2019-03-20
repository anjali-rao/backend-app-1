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


# Defaults
OCCUPATION_DEFAULT_CHOICE = 3
DEFAULT_USER_TYPE = 'subscriber'
DEFAULT_ENTERPRISE = 'Goplannr'
DEFAULT_BASE_PREMIUM = 0.0
DEFAULT_GST = 0.18
DEFAULT_COMMISSION = 0.20

DOC_TYPES = ('pan', 'license', 'photo')
DOCS_UPLOAD_TYPES = {
    'pan': 'advisor/pan',
    'license': 'advisor/license',
    'photo': 'advisor/selfie'
}

# Success messages
OTP_MESSAGE = 'Your One Time Password for GoPlannr is : %s'
OTP_SUCCESS = 'OTP verified successfully.'
OTP_GENERATED = 'OTP send successfully.'
AUTHORIZATION_GENERATED = 'Authorization key generated successfully.'
PASSWORD_CHANGED = 'Password changed successfully.'
USER_CREATION_MESSAGE = 'Hi, Your account with GoPlannr has been created successfully.\nYour username is %s generated under phone no %s.\n\nRegards\nTeam GoPlannr' # noqa
USER_CREATED_SUCESS = 'User created successfully!'

# TTL's (seconds)
OTP_TTL = 1800
TRANSACTION_TTL = 180

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

USER_CREATION_FIELDS = (
    'username', 'password', 'first_name', 'last_name', 'email',
    'referral_code', 'referral_reference', 'user_type'
)

# Upload paths
COMPANY_UPLOAD_PATH = 'company'
ENTERPRISE_UPLOAD_PATH = 'enterprise'
CATEGORY_UPLOAD_PATH = 'category'
