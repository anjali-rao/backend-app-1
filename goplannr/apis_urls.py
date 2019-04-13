from django.urls import path, include

urlpatterns = [
    path('', include('users.urls')),
    path('', include('content.urls')),
    path('', include('product.urls')),
    path('', include('questionnaire.urls')),
    path('', include('sales.urls')),
    path('', include('crm.urls'))
]
