from django.urls import path

from users.views import (
    RegisterUser, verify_otp, generate_otp, generate_authorization,
    update_password, SearchAccount, PincodeSearch, ContactUsAPI
)

urlpatterns = [
    path('user/otp/generate', generate_otp),
    path('user/otp/verify', verify_otp),
    path('user/register', RegisterUser.as_view()),
    path('user/authorization/generate', generate_authorization),
    path('user/update/password', update_password),
    path('users/account/search', SearchAccount.as_view()),
    path('pincode/search', PincodeSearch.as_view()),
    path('contact-us', ContactUsAPI.as_view())
]
