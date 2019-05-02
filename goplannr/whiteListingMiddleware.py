from django.core.exceptions import PermissionDenied
from users.models import IPAddress


class AuthIPWhitelistMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        response = None
        response = self.process_request(request)
        response = self.get_response(request)
        return response

    def process_request(self, request):
        auth_needed = dict(is_authentication_required=True)
        # Check if IP is whitelisted
        if self._is_ip_whitelisted(request):
            auth_needed['is_authentication_required'] = False
        if self._is_blocked(request):
            raise PermissionDenied
        request.META.update(auth_needed)
        return

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if not x_forwarded_for:
            return request.META.get('REMOTE_ADDR')
        # If there is a list of IPs provided, use the last one.
        return x_forwarded_for.split(',')[-1].strip()

    def _get_whitelisted_networks(self):
        return IPAddress._get_whitelisted_networks()

    def _is_ip_whitelisted(self, request):
        """
            Check if IP is on the whitelisted network.
        """
        self.client_ip = self._get_client_ip(request)
        if self.client_ip in self._get_whitelisted_networks():
            self._ip = IPAddress.objects.get(ip_address=self.client_ip)
            return not self._ip.authentication_required
        IPAddress.objects.get_or_create(ip_address=self.client_ip)
        return False

    def _is_blocked(self, request):
        return IPAddress.objects.get(ip_address=self.client_ip).blocked
