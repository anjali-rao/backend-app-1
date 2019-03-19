GENDER = ('male', 'female', 'transgender')
USER_TYPE = ('enterprise', 'subscriber', 'pos')
CITY_TIER = ((0, 'First'), (1, 'Second'), (2, 'Third'))

USER_CATEGORIES = {}
USER_FLAG = {'blacklist': False, 'training': False, 'exam_passed': None}

# Defaults
DEFAULT_USER_TYPE = 'subscriber'
DEFAULT_ENTERPRISE = 'Goplannr'

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
