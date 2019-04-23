from sales.models import Application


def update_insurance_fields(application_id):
    app = Application.objects.get(id=application_id)
    if hasattr(app, app.application_type):
        insurance = getattr(app, app.application_type)
        insurance.update_default_fields(
            dict.fromkeys(
                app.active_members.values_list('id', flat=True), False)
        )
