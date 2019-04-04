from django.urls import path

from product.views import (
    get_user_categories, GetSearchParamater
)

urlpatterns = [
    path('user/search/paramaters', GetSearchParamater.as_view()),
    path('user/product/categories', get_user_categories)
]
