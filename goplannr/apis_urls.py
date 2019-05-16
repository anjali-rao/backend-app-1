from django.urls import re_path, include

urlpatterns = [
    re_path('(?P<version>(v1|v2|v3))/', include('users.urls')),
    re_path('(?P<version>(v1|v2|v3))/', include('content.urls')),
    re_path('(?P<version>(v1|v2|v3))/', include('product.urls')),
    re_path('(?P<version>(v1|v2|v3))/', include('questionnaire.urls')),
    re_path('(?P<version>(v1|v2|v3))/', include('sales.urls')),
    re_path('(?P<version>(v1|v2|v3))/', include('crm.urls'))
]
