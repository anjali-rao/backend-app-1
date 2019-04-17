from rest_framework import exceptions, status


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
