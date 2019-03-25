from django.conf.urls import url

from product.views import (
    get_user_categories, GetSearchParamater
)

urlpatterns = [
	url(r'user/search/paramaters$', GetSearchParamater.as_view()),
    url(r'user/product/categories$', get_user_categories)
]
