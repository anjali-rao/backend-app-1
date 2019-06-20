from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django import views
from django.http import JsonResponse

from payment.models import ApplicationPayment, ApplicationRequestLog
from goplannr.settings import ENV, DEBUG


class AdityaBirlaPaymentGateway(views.View):
    template_name = 'aditya_birla.html'
    _secSignature = 'fed47b72baebd4f5f98a3536b8537dc4e17f60beeb98c77c97dadc917004b3bb' # noqa
    return_url = '%s://payment.%s/health/adityabirla/capture?application_id=%s'
    _summary_url = 'https://wallnut.in/health/proposal/proposal_summary/aditya_birla/1?proposal_id=%s&customer_id=%s' # noqa
    company_name = 'AdityaBirlaHealthInsurance'

    def get(self, request, *args, **kwargs):
        try:
            from aggregator.wallnut.models import Application
            app = Application.objects.get(id=kwargs['pk'])
            if app.company_name != self.company_name:
                raise PermissionDenied()
            if request.is_ajax():
                context = dict(
                    email=app.reference_app.client.email,
                    phone_no=app.reference_app.client.phone_no,
                    source_code='WMGR0026', premium=app.premium,
                    secSignature=self._secSignature,
                    return_url=self.return_url % (
                        'http' if DEBUG else 'https', ENV, app.id))
                context.update(self.get_paramaters(app))
                ApplicationRequestLog.objects.create(
                    application_id=app.reference_app.id,
                    url=self.return_url, payload=context)
                return JsonResponse(context, status=200)
            if app.payment_captured:
                return render(request, 'successful.html', dict(app=app))
            return render(request, self.template_name)
        except (KeyError, Application.DoesNotExist):
            pass
        raise PermissionDenied()

    def get_paramaters(self, app):
        import re
        import requests
        url = self._summary_url % (app.proposal_id2, app.customer_id)
        res = requests.get(url)
        page_content = str(res.content)
        patterns = dict(
            source_txn_id=re.compile(r'id="SourceTxnId" value="(\w*)'),
            quote_id=re.compile(r'id="QuoteId" value="(\w*)'),
            SourceCode=re.compile(r'id="SourceCode" value="(\w*)'),
            secSignature=re.compile(r'id="secSignature" value="(\w*)')
        )
        for pattern in patterns.keys():
            patterns[pattern] = patterns[pattern].findall(page_content)[0]
        return patterns


class AdityaBirlaPaymentCapture(views.View):
    capture_url = 'https://wallnut.in/health/proposal/confirm/aditya_birla'
    template_name = 'successful.html'
    app = None

    @method_decorator(views.decorators.csrf.csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(AdityaBirlaPaymentCapture, self).dispatch(
            request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from aggregator.wallnut.models import Application
        self.app = Application.objects.get(id=request.GET['application_id'])
        ApplicationRequestLog.objects.create(
            application_id=self.app.reference_app.id,
            url=request.build_absolute_uri(), response=request.POST.dict(),
            request_type=request.method)
        ApplicationPayment.objects.create(
            application_id=self.app.reference_app.id,
            merchant_txn_id=request.POST['merchantTxnId'],
            amount=request.POST['amount'],
            payment_mode=request.POST['paymentMode'],
            status=request.POST['TxStatus'],
            transaction_id=request.POST['SourceTxnId'],
            transaction_reference_no=request.POST['TxRefNo'],
            response=request.POST.dict())
        self.create_commission()
        import requests
        data = request.POST.dict()
        requests.post(self.capture_url, data=data)
        reference_app = self.app.reference_app
        reference_app.stage = 'completed'
        reference_app.status = 'completed'
        reference_app.save()
        policy = reference_app.create_policy()
        policy.policy_data = data
        policy.save()
        self.app.payment_captured = True
        self.app.save()
        return render(request, self.template_name, dict(app=self.app))

    def create_commission(self):
        from earnings.models import Commission
        cc = self.app.reference_app.quote.premium.product_variant.company_category # noqa
        commission = self.app.reference_app.quote.premium.commission + cc.company.commission + cc.category.commission + self.app.reference_app.quote.lead.user.enterprise.commission # noqa
        Commission.objects.create(
            application_id=self.app.reference_app.id,
            amount=self.app.premium * commission)


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
            if app.regenerate_payment_link:
                app.insurer_product.perform_creation()
                app.regenerate_payment_link = True
                app.save()
            context = self.get_paramaters(app)
            context.update(dict(
                customer_email=app.reference_app.client.email,
                customer_name=app.reference_app.client.get_full_name(),
                premium=int(app.premium)))
            ApplicationRequestLog.objects.create(
                application_id=app.reference_app.id,
                payload=context, request_type='POST')
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


class BajajAlianzGICGateway(views.View):
    template_name = 'bajaj_allianz_gic_health.html'
    _summary_url = 'https://wallnut.in/health/proposal/proposal_summary/bajaj_allianz/14?proposal_id=%s&customer_id=%s' # noqa
    company_name = 'BajajAllianzGeneralInsuranceCoLtd'

    def get(self, request, *args, **kwargs):
        from aggregator.wallnut.models import Application
        try:
            app = Application.objects.get(id=kwargs['pk'])
            if app.company_name != self.company_name:
                raise PermissionDenied()
            if request.is_ajax():
                app.insurer_product.perform_creation()
                context = dict(payment_link=self.get_paramaters(app))
                return JsonResponse(context, status=200)
            return render(request, self.template_name)
        except (KeyError, Application.DoesNotExist):
            pass
        raise PermissionDenied()

    def get_paramaters(self, app):
        import re
        import requests
        url = self._summary_url % (app.proposal_id, app.customer_id)
        res = requests.get(url)
        page_content = str(res.content)
        p = re.compile(r'name="payment_link" id="payment_link" value="(.*)"/>')
        payment_link = p.findall(page_content)[0]
        return payment_link
