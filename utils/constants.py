GENDER = ('male', 'female', 'transgender')
USER_TYPE = ('enterprise', 'subscriber', 'pos')
USER_CATEGORIES = {}
USER_FLAG = {'blacklist': False, 'training': False, 'exam_passed': None}
DOC_TYPES = ('pan', 'license', 'photo')
DOCS_UPLOAD_TYPES = {
    'pan': 'media/advisor/pan',
    'license': 'media/advisor/license',
    'photo': 'media/advisor/selfie'
}

POST_REQUEST_ONLY = ['put', 'delete']

# Exception messages
REFERRAL_CODE_EXCEPTION = 'Invalid referral code provided.'
USER_CREATION_FIELDS = (
    'username', 'password', 'first_name', 'last_name', 'email',
    'referral_code', 'referral_reference', 'user_type'
)
