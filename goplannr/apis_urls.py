from django.urls import re_path, include

urlpatterns = [
    re_path('(?P<version>(v1|v2))/', include('users.urls')),
    re_path('(?P<version>(v1|v2))/', include('content.urls')),
    re_path('(?P<version>(v1|v2))/', include('product.urls')),
    re_path('(?P<version>(v1|v2))/', include('questionnaire.urls')),
    re_path('(?P<version>(v1|v2))/', include('sales.urls')),
    re_path('(?P<version>(v1|v2))/', include('crm.urls'))
]
