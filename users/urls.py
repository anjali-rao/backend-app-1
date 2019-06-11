from django.urls import path

from users.views import (
    RegisterUser, verify_otp, generate_otp, generate_authorization,
    update_password, SearchAccount, PincodeSearch, GetEarnings,
    GetLeads, GetClients, GetCart, GetPlaylist, UpdateUser,
    GetUserDetails, CreateAppointment
)

urlpatterns = [
    path('user/otp/generate', generate_otp),
    path('user/otp/verify', verify_otp),
    path('user/register', RegisterUser.as_view()),
    path('user/authorization/generate', generate_authorization),
    path('user/update/password', update_password),
    path('user/update', UpdateUser.as_view()),
    path('user/leads', GetLeads.as_view()),
    path('user/clients', GetClients.as_view()),
    path('user/cart', GetCart.as_view()),
    path('user/playlist', GetPlaylist.as_view()),
    path('user/earnings', GetEarnings.as_view()),
    path('user/<slug:pk>/details', GetUserDetails.as_view()),
    path('user/appointment/create', CreateAppointment.as_view()),
    path('users/account/search', SearchAccount.as_view()),
    path('pincode/search', PincodeSearch.as_view()),
]
