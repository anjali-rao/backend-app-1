from celery import shared_task


@shared_task(name='sales.tasks.update_insurance_fields')
def update_insurance_fields(application_id):
    from sales.models import Application
    app = Application.objects.get(id=application_id)
    if hasattr(app, app.application_type):
        insurance = getattr(app, app.application_type)
        data = list()
        members = app.active_members or app.member_set.all()
        for member_id in members.values_list('id', flat=True):
            data.append({"id": member_id, "value": False})
        insurance.update_default_fields(data)


@shared_task(name='sales.tasks.mark_ignore_rejected_quotes')
def mark_ignore_rejected_quotes():
    """
    This task will mark ignore all rejected quotes.
    Quote will be eligible to be marked as ignore after
    24 hrs marked as ignore
    """
    from django.utils.timezone import now
    from dateutil.relativedelta import relativedelta
    from sales.models import Quote
    quotes = Quote.objects.filter(
        status='rejected', modified__gte=now() - relativedelta(hours=24),
        ignore=False)
    quotes.update(ignore=True)


@shared_task(name='sales.tasks.aggregator_operation')
def aggregator_operation(application):
    application.aggregator_operation()
