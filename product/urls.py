from django.conf.urls import url

from product.views import (
    get_user_categories
)

urlpatterns = [
    url(r'user/product/categories$', get_user_categories)
]
