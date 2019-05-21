
def evaluateClassName(className, insuranceType):
    from aggregator.wallnut.health.aditya_birla import (
        AdityaBirlaHealthInsurance)

    HEALTH_CLASS_MAPPING = dict(
        AdityaBirlaHealthInsurance=AdityaBirlaHealthInsurance
    )

    INSURANCE_CATEGORY_MAPPING = dict(
        healthinsurance=HEALTH_CLASS_MAPPING
    )

    return INSURANCE_CATEGORY_MAPPING[insuranceType][className]
