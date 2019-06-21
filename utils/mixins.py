from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import (
    NotAcceptable, NotFound, MethodNotAllowed)
from rest_framework import exceptions, status
from rest_framework.views import exception_handler


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

        raise MethodNotAllowed(self.request.method)


class APIException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        'detail': ['Service temporarily unavailable, try again later.']
    }
    default_code = 'invalid'


class RecommendationException(Exception):
    pass


class InsuranceException(Exception):
    pass


class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data
        response.data = dict()
        errors = []
        for field, value in data.items():
            errors.extend(value)
        if 'detail' not in data:
            exc = ' & '.join(errors)
        response.data['detail'] = str(exc)
    return response
