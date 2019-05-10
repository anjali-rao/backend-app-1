from rest_framework import exceptions, status
from django.utils.translation import ugettext_lazy as _
from rest_framework.pagination import PageNumberPagination


class MethodSerializerView(object):
    '''
    Utility class for get different serializer class by method.
    For example:
    method_serializer_classes = {
        ('GET', ): MyModelListViewSerializer,
        ('PUT', 'PATCH'): MyModelCreateUpdateSerializer
    }
    '''
    method_serializer_classes = None

    def get_serializer_class(self):
        assert self.method_serializer_classes is not None, (
            'Expected view %s should contain method_serializer_classes '
            'to get right serializer class.' %
            (self.__class__.__name__, )
        )
        for methods, serializer_cls in self.method_serializer_classes.items():
            if self.request.method in methods:
                return serializer_cls

        raise exceptions.MethodNotAllowed(self.request.method)


class APIException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'detail': ['Service temporarily unavailable, try again later.']
    }
    default_code = 'invalid'

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        # For validation failures, we are overriding details to dict from str,
        # so that error response should remain common across all errors.
        if not isinstance(detail, dict):
            detail = {'detail': [detail]}

        self.detail = exceptions._get_error_details(detail, code)


class NotAcceptable(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = _('Could not satisfy the request Accept header.')
    default_code = 'not_acceptable'

    def __init__(self, detail=None, code=None, available_renderers=None):
        self.available_renderers = available_renderers
        super(NotAcceptable, self).__init__(detail, code)


class NotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('Not found.')
    default_code = 'not_found'


class RecommendationException(Exception):
    pass


class InsuranceException(Exception):
    pass


class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
