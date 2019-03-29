from django.conf.urls import url

from users.views import (
    RegisterUser, verify_otp, generate_otp, generate_authorization,
    update_password, SearchAccount, PincodeSearch
)

urlpatterns = [
    url(r'user/otp/generate', generate_otp),
    url(r'user/otp/verify', verify_otp),
    url(r'user/register', RegisterUser.as_view()),
    url(r'user/authorization/generate', generate_authorization),
    url(r'user/update/password', update_password),
    url(r'users/account/search', SearchAccount.as_view()),
    url(r'pincode/search', PincodeSearch.as_view()),
]
