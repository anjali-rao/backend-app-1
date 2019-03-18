from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions


class UserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        message = 'Authorization not provided.'
        from users.models import User
        user = User.get_authenticated_user(
            request.META.get('HTTP_AUTHORIZATION'))
        if user:
            return (user, None)
        message = 'Invalid authentication token provided'
        raise exceptions.AuthenticationFailed(message)
