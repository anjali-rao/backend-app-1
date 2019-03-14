from django.conf.urls import url

from users.views import RegisterUser

urlpatterns = [
    url(r'user/register', RegisterUser.as_view()),
]
