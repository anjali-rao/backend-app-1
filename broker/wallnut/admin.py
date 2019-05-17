from django.contrib import admin

from broker.wallnut.models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'reference_app', 'section', 'premium', 'user_id', 'proposer_id')
    search_fields = (
        'reference_app__reference_no', 'reference_app_id', 'user_id',
        'proposer_id')
    raw_id_fields = ('reference_app',)
    list_filter = ('section',)
