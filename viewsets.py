from rest_framework.response           import Response
from rest_framework.decorators         import action
from rest_framework                    import status
from rest_framework.viewsets           import GenericViewSet
from rest_framework.exceptions         import NotAuthenticated, PermissionDenied
from rest_framework.mixins             import (
    RetrieveModelMixin, 
    CreateModelMixin, 
    UpdateModelMixin, 
    ListModelMixin
)

from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from .exceptions                       import (
    ObjectDoesNotExistException,
    InternalServerErrorException, 
    PermissionDeniedException,
    NotauthenticatedException
)

class BaseViewSet(CreateModelMixin,
                    ListModelMixin,
                    UpdateModelMixin, 
                    RetrieveModelMixin, 
                    GenericViewSet):
    authentication_classes = [JSONWebTokenAuthentication]

    def get_object(self):
        '''
            커스텀 예외처리
        '''
        try:
            queryset = self.filter_queryset(self.get_queryset())
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
            obj = queryset.get(**filter_kwargs)
            self.check_object_permissions(request=self.request, obj=obj)
            return obj
        except NotAuthenticated:
            raise NotauthenticatedException()
        except PermissionDenied:
            raise PermissionDeniedException()
        except self.model_class.DoesNotExist as e:
            raise ObjectDoesNotExistException(message=e)
        except Exception as e:
            raise InternalServerErrorException(message=e)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        service  = self.service_class(serializer=self.get_serializer())
        instance = service.update(instance=self.get_object())
        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)
    
    def create(self, request, *args, **kwargs) -> Response:
        service  = self.service_class(serializer=self.get_serializer())
        instance = service.create()
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put'])
    def field(self, request, pk):
        service  = self.service_class(serializer=self.get_serializer())
        instance = service.update(instance=self.get_object(), partial=True)
        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)
