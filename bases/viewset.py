from commons.exceptions                import PermissionDeniedException, NotauthenticatedException
from commons.permissions               import IsOwnerOrHouseholdMemberReadOnly
from rest_framework                    import viewsets
from rest_framework_jwt.authentication import JSONWebTokenAuthentication


class BaseGenericViewSet(viewsets.GenericViewSet):
    service_class = None
    authentication_classes = [JSONWebTokenAuthentication]
    permission_classes = (IsOwnerOrHouseholdMemberReadOnly, )

    def __init__(self, *args, **kwargs):
        assert self.service_class, f"{self.__class__.__name__} not set service class."
        super().__init__(*args, **kwargs)

    def permission_denied(self, request, message=None, code=None):
        if request.authenticators and not request.successful_authenticator:
            raise NotauthenticatedException(message=message, code=code)
        raise PermissionDeniedException(message=message, code=code)

    def get_service(self):
        return self.service_class()
        
    def get_object(self):
        assert self.lookup_field in self.kwargs, (
            '"{class_name}" be called with '
            'invalid URL keyword argument "{field_name}". '.format(
                class_name=self.__class__.__name__, 
                field_name=self.lookup_field
            )
        )
        service = self.get_service()
        obj = service.get_by_model_id(model_id=self.kwargs[self.lookup_field])
        self.check_object_permissions(request=self.request, obj=obj)
        return obj
