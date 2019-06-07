from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import (
    APIException, NotAcceptable, NotFound, MethodNotAllowed)


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


class RecommendationException(Exception):
    pass


class InsuranceException(Exception):
    pass


class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
