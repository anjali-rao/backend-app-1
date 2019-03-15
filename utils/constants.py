GENDER = ('male', 'female', 'transgender')
USER_TYPE = ('enterprise', 'subscriber', 'pos')
USER_CATEGORIES = {}
USER_FLAG = {'blacklist': False, 'training': False, 'exam_passed': None}
DEFAULT_USER_TYPE = 'subscriber'

DOC_TYPES = ('pan', 'license', 'photo')
DOCS_UPLOAD_TYPES = {
    'pan': 'media/advisor/pan',
    'license': 'media/advisor/license',
    'photo': 'media/advisor/selfie'
}

# Success messages
OTP_MESSAGE = 'Your One Time Password for GoPlannr is : %s'
OTP_SUCCESS = 'OTP verified successfully.'
OTP_GENERATED = 'OTP send successfully.'
AUTHORIZATION_GENERATED = 'Authorization key generated successfully.'
PASSWORD_CHANGED = 'Password changed successfully.'

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

USER_CREATION_FIELDS = (
    'username', 'password', 'first_name', 'last_name', 'email',
    'referral_code', 'referral_reference', 'user_type'
)
