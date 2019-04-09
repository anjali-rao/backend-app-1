from django.urls import path, include, re_path
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    re_path('(?P<version>(v1|v2))/', include('goplannr.apis_urls')),
    path('', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
