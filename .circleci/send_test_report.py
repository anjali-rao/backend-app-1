
def send_report():
    import requests
    with open('.circleci/test_report.log', 'rb') as report:
        requests.post(
            "https://hooks.slack.com/services/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", # noqa
            json=dict(text=report.read()))
return 'OK'
