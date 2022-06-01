from commons.exceptions            import PermissionDeniedException, NotauthenticatedException
from rest_framework                import viewsets
from rest_framework.authentication import SessionAuthentication, BasicAuthentication


class BaseGenericViewSet(viewsets.GenericViewSet):
    service_class = None
    lookup_field = 'id'
    authentication_class = [SessionAuthentication, BasicAuthentication]

    def __init__(self, *args, **kwargs):
        assert self.service_class, f"{self.__class__.__name__} not set service class."
        self.service = self.service_class()
        super().__init__(*args, **kwargs)

    def permission_denied(self, request, message=None, code=None):
        if request.authenticators and not request.successful_authenticator:
            raise NotauthenticatedException(message=message, code=code)
        raise PermissionDeniedException(message=message, code=code)

    def check_object_permissions(self, request, obj):
        """
            object를 위한 인증
        """
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request,
                    message=getattr(permission, 'message', None),
                    code=getattr(permission, 'code', None)
                )
        
    def get_object(self):
        assert self.lookup_field in self.kwargs, (
            '"{class_name}" be called with '
            'invalid URL keyword argument "{field_name}". '.format(
                class_name=self.__class__.__name__, 
                field_name=self.lookup_field
            )
        )
        obj = self.service.get(**self.kwargs)
        self.check_object_permissions(request=self.request, obj=obj)
        return obj

    def get_queryset(self, **kwargs):
        queryset = self.service.filter(**kwargs)
        return queryset
