from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django import views
from django.http import HttpResponse

from payment.models import Payment, ApplicationRequestLog


class AdityaBirlaPaymentGateway(views.View):
    template_name = 'aditya_birla.html'
    _secSignature = 'fed47b72baebd4f5f98a3536b8537dc4e17f60beeb98c77c97dadc917004b3bb' # noqa
    return_url = 'http://payment.localhost:8000/health/adityabirla/capture?application_id=%s' # noqa
    _summary_url = 'https://wallnut.in/health/proposal/proposal_summary/aditya_birla/1?proposal_id=%s&customer_id=%s' # noqa
    company_name = 'AdityaBirlaHealthInsurance'

    def get(self, request, *args, **kwargs):
        try:
            from aggregator.wallnut.models import Application
            app = Application.objects.get(id=kwargs['pk'])
            if app.company_name != self.company_name:
                raise PermissionDenied()
            context = dict(
                email=app.reference_app.client.email,
                phone_no=app.reference_app.client.phone_no,
                source_code='WMGR0026', premium=1,  # app.premium,
                secSignature=self._secSignature,
                return_url=self.return_url % app.id,
                source_txn_id=self.get_transaction_id(app)
            )
            ApplicationRequestLog.objects.create(
                application_id=app.reference_app.id,
                url=self.return_url, payload=context
            )
            return render(request, self.template_name, context)
        except (KeyError, Application.DoesNotExist):
            pass
        raise PermissionDenied()

    def get_transaction_id(self, app):
        import re
        import requests
        url = self._summary_url % (
            app.proposal_id2, app.customer_id)
        res = requests.get(url)
        page_content = str(res.content)
        pattern = re.compile(r'id="SourceTxnId" value="(\w*)')
        return pattern.findall(page_content)[0]


class AdityaBirlaPaymentCapture(views.View):
    capture_url = 'https://wallnut.in/health/proposal/confirm/aditya_birla'

    @method_decorator(views.decorators.csrf.csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(AdityaBirlaPaymentCapture, self).dispatch(
            request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        ApplicationRequestLog.objects.create(
            application_id=kwargs.get('application_id'),
            url=request.url, response=request.POST.dict(),
            request_type=request.METHOD
        )
        Payment.objects.create(
            application_id=kwargs.get('application_id'),
            merchant_txn_id=request.POST['merchantTxnId'],
            amount=request.POST['amount'],
            payment_mode=request.POST['paymentMode'],
            status=request.POST['TxStatus'],
            transaction_id=request.POST['SourceTxnId'],
            transaction_reference_no=request.POST['TxRefNo'],
            response=request.POST.dict()
        )
        import requests
        requests.post(self.capture_url, data=request.POST)
        return HttpResponse("Payment successfully processed.")


class HDFCPaymentGateway(views.View):
    template_name = 'hdfc_ergo_health.html'
    _summary_url = 'https://wallnut.in/health/proposal/proposal_summary/hdfc_ergo/4?proposal_id=%s&customer_id=%s' # noqa
    company_name = 'HDFCERGOGeneralInsuranceCoLtd'

    def get(self, request, *args, **kwargs):
        from aggregator.wallnut.models import Application
        try:
            app = Application.objects.get(id=kwargs['pk'])
            if app.company_name != self.company_name:
                raise PermissionDenied()
            context = self.get_paramaters(app)
            context.update(dict(
                customer_email=app.reference_app.client.email,
                customer_name=app.reference_app.client.get_full_name(),
                premium=int(app.premium)
            ))
            ApplicationRequestLog.objects.create(
                application_id=app.reference_app.id,
                payload=context, request_type='POST'
            )
            return render(request, self.template_name, context)
        except (KeyError, Application.DoesNotExist):
            pass
        raise PermissionDenied()

    def get_paramaters(self, app):
        import re
        import requests
        url = self._summary_url % (app.proposal_id, app.customer_id)
        res = requests.get(url)
        page_content = str(res.content)
        patterns = dict(
            customer_code=re.compile(r'id="CustomerID" value="(\w*)'),
            additionalInfo1=re.compile(r'id="AdditionalInfo1" value="(\w*)'),
            additionalInfo2=re.compile(r'id="AdditionalInfo2" value="(\w*)'),
            additionalInfo3=re.compile(r'id="AdditionalInfo3" value="(\w*)'),
            product_code=re.compile(r'id="ProductCd" value="(\w*)'),
            producer_code=re.compile(r'id="ProducerCd" value="(\w*)')
        )
        for pattern in patterns.keys():
            patterns[pattern] = patterns[pattern].findall(page_content)[0]
            setattr(app, pattern, patterns[pattern])
        app.save()
        return patterns
