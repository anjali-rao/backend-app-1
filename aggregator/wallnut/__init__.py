
def evaluateClassName(className, insuranceType):
    from aggregator.wallnut.health.aditya_birla import (
        AdityaBirlaHealthInsurance)
    from aggregator.wallnut.health.hdfc_ergo import HDFCERGOHealthInsurance

    HEALTH_CLASS_MAPPING = dict(
        AdityaBirlaHealthInsurance=AdityaBirlaHealthInsurance,
        HDFCERGOGeneralInsuranceCoLtd=HDFCERGOHealthInsurance
    )

    INSURANCE_CATEGORY_MAPPING = dict(
        healthinsurance=HEALTH_CLASS_MAPPING
    )

    return INSURANCE_CATEGORY_MAPPING[insuranceType][className]
