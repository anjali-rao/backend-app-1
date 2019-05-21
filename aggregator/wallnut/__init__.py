
def evaluateClassName(className):
    from aggregator.wallnut.insurer.aditya_birla import AdityaBirlaHealthInsurance

    CLASS_MAPPING = dict(
        AdityaBirlaHealthInsurance=AdityaBirlaHealthInsurance
    )
    return CLASS_MAPPING.get(className)
