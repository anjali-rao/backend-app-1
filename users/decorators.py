from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions


class UserAuthentication(BaseAuthentication):

    def authenticate(self, request):
        if not request.META['is_authentication_required']:
            return (None, None)
        from users.models import User
        message = 'Authorization not provided.'
        if 'HTTP_AUTHORIZATION' in request.META:
            user = User.get_authenticated_user(
                request.META['HTTP_AUTHORIZATION'])
            if user:
                return (user, None)
            message = 'Invalid authorization passed.'
        raise exceptions.AuthenticationFailed(message)
