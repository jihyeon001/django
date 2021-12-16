import uuid
import time
from datetime        import datetime
from config.settings import ADMIN
from .exceptions     import (
    KeyErrorException, 
    ObjectDoesNotExistException,
    InternalServerErrorException, 
    PermissionDeniedException,
    NotauthenticatedException
)

from django.db                         import models
from django.utils.safestring           import mark_safe
from django.contrib.auth.base_user     import BaseUserManager
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.response           import Response
from rest_framework                    import status
from rest_framework.exceptions         import NotAuthenticated, PermissionDenied
from rest_framework.decorators         import action
from rest_framework.viewsets           import GenericViewSet
from rest_framework.mixins             import (
    RetrieveModelMixin, 
    CreateModelMixin, 
    UpdateModelMixin, 
    ListModelMixin
)

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, **validated_data):
        """
            Create and save a user with the given username, password.
        """
        password = validated_data.pop('password', None)
        if password is None:
            raise KeyErrorException('password')
        user = self.model(**validated_data)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, **validated_data):
        validated_data.setdefault('username', ADMIN['USERNAME'])
        validated_data.setdefault('password', ADMIN['PASSWORD'])
        validated_data.setdefault('is_staff', True)
        validated_data.setdefault('is_superuser', True)
        return self.create_user(**validated_data)

class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset() #.filter(active=True)

class BaseModel(models.Model):
    """
        This model defines base models that implements common fields
    """
    objects         = BaseModelManager()
    id              = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    created_at      = models.IntegerField(default=0)
    updated_at      = models.IntegerField(default=0)
    
    MANY_TO_ONE_RELATIONS  = tuple()
    ONE_TO_ONE_RELATIONS   = tuple()
    ONE_TO_MANY_RELATIONS  = tuple()
    MANY_TO_MANY_RELATIONS = tuple()
    class Meta:
        abstract=True

    @classmethod
    def get_model_objects(cls, excludes=()):
        """
            모델에 필드와 함께 명시한 Relations 필드로
            viewset의 get_queryset() 이전에 
            select_related와 prefetch_related를 적용
        """
        Model_Objects = cls._default_manager
        select_fields = [field for field in cls.get_select_fields() if not field in excludes]
        prefetch_fields = [field for field in cls.get_prefetch_fields() if not field in excludes]

        if select_fields:
            Model_Objects = Model_Objects.select_related(*select_fields)
        if prefetch_fields:
            Model_Objects = Model_Objects.prefetch_related(*prefetch_fields)
        return Model_Objects

    @classmethod
    def get_select_fields(cls):
        return cls.MANY_TO_ONE_RELATIONS + cls.ONE_TO_ONE_RELATIONS

    @classmethod
    def get_prefetch_fields(cls):
        return cls.MANY_TO_MANY_RELATIONS + cls.ONE_TO_MANY_RELATIONS

    def save(self, *args, **kwargs):
        self.updated_at = int(time.time())
        if not self.created_at:
            self.created_at = int(time.time())
        return super().save(*args, **kwargs)

    def create_datetime(self):
        """
            unixtimestamp, admin에서 datetime
        """
        return mark_safe(datetime.fromtimestamp(self.created_at).strftime('%Y-%m-%d %H:%M:%S'))
    def update_datetime(self):
        return mark_safe(datetime.fromtimestamp(self.updated_at).strftime('%Y-%m-%d %H:%M:%S'))

class BaseService:
    def __init__(self, serializer):
        self.serializer = serializer
        self.model_class = serializer.Meta.model
        self.request = serializer.context.get('request', None)
        self.extract_relation = RelationExtraction(serializer=serializer)

    def check_validation(self, data, instance=None, partial=False):
        '''
            serializer로 유효성 체크
        '''
        serializer = self.serializer.__class__(
            instance=instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return data

    def update_many_to_many(self, instance, m2m_data):
        '''
            update m2m relation
            - 기존 값과 비교 후 변경사항이 있을 경우에만 작동
            - *arguments 처리해야 한번에 insert, delete 쿼리
        '''
        for key, m2m_instances in m2m_data.items():
            exists   = set(getattr(instance, key).all())
            updates  = set(m2m_instances)
            addeds   = updates - exists
            deleteds = exists - updates
            if addeds:
                getattr(instance, key).add(*addeds)
            if deleteds:
                getattr(instance, key).remove(*deleteds)

    def create(self):
        '''
            input data에서 m2m relarion field만 분리
            유효성 체크 후 생성
        '''
        data, m2m_data = self.extract_relation.separate_data(data=self.request.data)
        validated_data = self.check_validation(data=data)
        model_manager = self.model_class.objects
        if hasattr(model_manager, 'create_user'):
            instance = model_manager.create_user(**validated_data)
        else:
            instance = model_manager.create(**validated_data)
        
        if m2m_data:
            self.update_many_to_many(instance=instance, m2m_data=m2m_data)        
        return instance

    def update(self, instance, partial=False):
        '''
            변경사항이 있는 필드만 update
        '''
        data, m2m_data = self.extract_relation.separate_data(data=self.request.data)
        if data:
            validated_data = self.check_validation(
                data=data, instance=instance, partial=partial)
            update_field_count = 0
            for key, val in validated_data.items():
                if getattr(instance, key) != val:
                    setattr(instance, key, val)
                    update_field_count += 1
            
            if update_field_count > 0:
                instance.save()
        if m2m_data:
            self.update_many_to_many(instance=instance, m2m_data=m2m_data)
        return instance

class RelationExtraction:
    def __init__(self, serializer):
        '''
            모델 class에서 relations 상수 설정이 되어있어야 작동
                초기엔 Model과 Serializer에서 필드정보를 추출했으나
                성능 측면과 명시적이지 않아 Model안에 명시하는 방식으로 변경
            
            -   rest_framework.utils.model_meta.get_field_info()의 경우
                필드 정보와 Relation 필드의 Model까지만 제공되고
                속도도 두배정도 소요 되어서 패스            
        '''
        self.serializer = serializer
        model_class = self.serializer.Meta.model
        self.many_to_many = model_class.MANY_TO_MANY_RELATIONS
        self.many_to_one = model_class.MANY_TO_ONE_RELATIONS

        # relation serializer 클래스 추출
        self.nested_serializer = dict()
        for key, val in self.serializer.get_fields().items():
            if key in self.many_to_many and hasattr(val, 'many'):
                self.nested_serializer[key] = val.child.__class__
            elif key in self.many_to_one and not hasattr(val, 'many'):
                self.nested_serializer[key] = val.__class__

    @staticmethod
    def get_relation_instance(serializer_class, dictionary):
        '''
            is_created = dictionary.pop('is_created', None)
            if is_created:
                serializer = serializer_class(data=dictionary)
                serializer.is_valid(raise_exception=True)
                instance = serializer.save()
                return instance
            - Retation 모델 생성 부분 제거
        '''
        relation_id = dictionary.pop('id', None)
        relation_model_class = serializer_class.Meta.model
        if relation_id:
            try:
                return relation_model_class._default_manager.get(id=relation_id)
            except relation_model_class.DoesNotExist as e:
                raise ObjectDoesNotExistException(message=e)
        else:
            raise KeyErrorException(message=relation_model_class.__name__)

    def get_many_to_one_instance(self, key, val):
        '''
            many_to_one 인스턴스 반환
        '''
        serializer = self.nested_serializer[key]
        return self.get_relation_instance(serializer_class=serializer, dictionary=val)

    def get_many_to_many_instances(self, key, val):
        '''
            many_to_many 인스턴스 반환
        '''
        serializer = self.nested_serializer[key]
        return [
            self.get_relation_instance(serializer_class=serializer, dictionary=nested_val)
        for nested_val in val]

    def separate_data(self, data):
        '''
            many to many relation - key : instance list
            many to one relation  - key : instance
        '''
        separated_m2m = dict()
        separated_data = dict()

        for key, val in data.items():
            if isinstance(val, dict) and key in self.many_to_one:
                separated_data[key] = self.get_many_to_one_instance(key=key, val=val)
            elif isinstance(val, list) and key in self.many_to_many:
                separated_m2m[key] = self.get_many_to_many_instances(key=key, val=val)
            else:
                separated_data[key] = val
        return separated_data, separated_m2m 
        
class BaseViewSet(CreateModelMixin,
                    ListModelMixin,
                    UpdateModelMixin, 
                    RetrieveModelMixin, 
                    GenericViewSet):
    authentication_classes = [JSONWebTokenAuthentication]

    def get_object(self):
        '''
            커스텀한 Exception class를 적용하기 위해 수정
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