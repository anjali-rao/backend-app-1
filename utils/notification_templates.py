
class Slack(object):
    payment_service = 'TFH7S6MPC/BKXE0QF89/zxso0BMKFFr3SFUVLpGBVcW9'

    OFFLINE_TRASACTION = 'Hi, Advisor %s opted for Offline mode for application # %s.\nVerify application details here %s.\n' # noqa
    ONLINE_TRANSACTION = 'Hi, Advisor %s process application with online mode for application # %s.\nFind application details here %s.\n' # noqa
    TRANSACTION_FAILURE = 'Hi, Advisor %s faces payment failure for application #%s.\nFind application details here %s.\n' # noqa
