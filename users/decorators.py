from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions


class UserAuthentication(BaseAuthentication):
    client_ip = None

    def authenticate(self, request):
        import pdb; pdb.set_trace()
        from users.models import User, IPAddress
        message = 'Authorization not provided.'
        self.client_ip = self._get_client_ip(request)
        if self.client_ip in IPAddress._get_whitelisted_networks():
            self._ip = IPAddress.objects.get(ip_address=self.client_ip)
            if not self._ip.authentication_required:
                return (None, None)
        if 'HTTP_AUTHORIZATION' in request.META:
            user = User.get_authenticated_user(
                request.META['HTTP_AUTHORIZATION'])
            if user:
                return (user, None)
            message = 'Invalid authorization passed.'
        raise exceptions.AuthenticationFailed(message)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if not x_forwarded_for:
            return request.META.get('REMOTE_ADDR')
        # If there is a list of IPs provided, use the last one.
        # This may not work on Google Cloud.
        return x_forwarded_for.split(',')[-1].strip()
