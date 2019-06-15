from rest_framework_swagger.views import get_swagger_view
from django.urls import re_path

schema_view = get_swagger_view(title='Pastebin API')

urlpatterns = [
    re_path(r'^$', schema_view)
]
