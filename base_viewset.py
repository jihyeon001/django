from .exceptions     import (
    InternalServerErrorException, 
    PermissionDeniedException,
    NotauthenticatedException,
    KeyErrorException
)

from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.viewsets           import GenericViewSet


class BaseGenericViewSet(GenericViewSet):
    authentication_classes = [JSONWebTokenAuthentication]
    repository_class = None
    service_class = None

    def __init__(self):
        if not self.repository_class or not self.service_class:
            raise InternalServerErrorException(
                message=f'"{self.__class__.__name__}" is not set repository or service class.'
            )
        super().__init__()

    def permission_denied(self, request, message=None, code=None):
        if request.authenticators and not request.successful_authenticator:
            raise NotauthenticatedException(message=message, code=code)
        raise PermissionDeniedException(message=message, code=code)

    def get_repository(self):
        return self.repository_class(model_class=self.serializer_class.Meta.model)

    def get_service(self):
        return self.service_class(user=self.request.user, repository=self.get_repository())
        
    def get_object(self):
        try:
            if not self.lookup_field in self.kwargs:
                raise KeyErrorException(
                    message=(
                        '"{class_name}" be called with '
                        'invalid URL keyword argument "{field_name}". '.format(
                            class_name=self.__class__.__name__, 
                            field_name=self.lookup_field
                        )
                    )
                )

            service = self.get_service()
            obj = service.get_by_model_id(model_id=self.kwargs[self.lookup_field])
            self.check_object_permissions(request=self.request, obj=obj)
            return obj
        except Exception as e:
            raise InternalServerErrorException(message=e)
