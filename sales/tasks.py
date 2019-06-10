from sales.models import Application
from celery import shared_task


@shared_task(name='sales.tasks.update_insurance_fields')
def update_insurance_fields(application_id):
    app = Application.objects.get(id=application_id)
    if hasattr(app, app.application_type):
        insurance = getattr(app, app.application_type)
        data = list()
        for member_id in app.active_members.values_list('id', flat=True):
            data.append({"id": member_id, "value": False})
        insurance.update_default_fields(data)
