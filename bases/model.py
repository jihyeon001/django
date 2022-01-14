import uuid
import time
from datetime    import datetime
from collections import OrderedDict, namedtuple

from django.db               import models
from django.contrib.auth     import get_user_model
from django.utils.safestring import mark_safe
from django.core.validators  import MaxValueValidator

MAX_UNIX_TIME_STAMP: int = 2147483647
MODEL_DATETIME_FORMAT : str = '%Y-%m-%d %H:%M:%S'

RelationInfo = namedtuple('RelationInfo', [
    'field',
    'related_model',
    'to_many',
    'reverse'
])
class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset() #.filter(is_active=True)

class BaseModel(models.Model):
    """
        model의 공통 field와 method를 정의
    """
    objects = BaseModelManager()
    id      = models.UUIDField(
        primary_key=True, 
        unique=True, 
        default=uuid.uuid4, 
        editable=False
    )
    created_at = models.IntegerField(
        default=0, 
        validators=[
            MaxValueValidator(MAX_UNIX_TIME_STAMP)
        ]
    )
    updated_at = models.IntegerField(
        default=0, 
        validators=[
            MaxValueValidator(MAX_UNIX_TIME_STAMP)
        ]
    )
    class Meta:
        abstract=True

    @classmethod
    def get_model_options(cls):
        return cls._meta.concrete_model._meta

    @classmethod
    def eager_objects(cls, excludes=()):
        """
            Relation field를 가져와 eager loading 적용
            - 30% 속도 개선
            - 제외할 필드를 excludes로 전달
        """
        Model_Objects = cls._default_manager
        opts = cls.get_model_options()
        many_to_one, many_to_many_forward, *_  = cls.get_forward_relationships(opts)
        one_to_many, many_to_many_reverse = cls.get_reverse_relationships(opts)

        select_fields = [field for field in many_to_one.keys() if not field in excludes]
        prefetch_fields = [field for field in \
                list(one_to_many.keys()) + \
                list(many_to_many_reverse.keys()) + \
                list(many_to_many_forward.keys())
            if not field in excludes]

        if select_fields:
            Model_Objects = Model_Objects.select_related(*select_fields)
        if prefetch_fields:
            Model_Objects = Model_Objects.prefetch_related(*prefetch_fields)
        return Model_Objects

    @staticmethod
    def get_forward_relationships(opts):
        """
            forward relation field의 정보를 RelationInfo에 담아
            many-to-one과 many-to-many를 분리하여 OrderedDict으로 반환
        """
        field_names = list()
        has_user_foreign_key = False
        many_to_one = OrderedDict()
        for field in opts.fields:
            field_name = field.name
            field_names.append(field_name)
            if field.serialize and field.remote_field:
                related_model = field.remote_field.model
                many_to_one[field_name] = RelationInfo(
                    field=field,
                    related_model=related_model,
                    to_many=False,
                    reverse=False
                )
                if related_model == get_user_model():
                    has_user_foreign_key = True
        # Deal with forward many-to-many relationships.
        many_to_many_forward = OrderedDict()
        for field in [field for field in opts.many_to_many if field.serialize]:
            many_to_many_forward[field.name] = RelationInfo(
                field=field,
                related_model=field.remote_field.model,
                to_many=True,
                reverse=False
            )
        return many_to_one, many_to_many_forward, field_names, has_user_foreign_key

    @staticmethod
    def get_reverse_relationships(opts):
        """
            reverse relation field의 정보를 RelationInfo에 담아 OrderedDict으로 반환
        """
        one_to_many = OrderedDict()
        for relation in [r for r in opts.related_objects if not r.field.many_to_many]:
            accessor_name = relation.get_accessor_name()
            one_to_many[accessor_name] = RelationInfo(
                field=None,
                related_model=relation.related_model,
                to_many=relation.field.remote_field.multiple,
                reverse=True
            )
        # Deal with reverse many-to-many relationships.
        many_to_many_reverse = OrderedDict()
        for relation in [r for r in opts.related_objects if r.field.many_to_many]:
            accessor_name = relation.get_accessor_name()
            many_to_many_reverse[accessor_name] = RelationInfo(
                field=None,
                related_model=relation.related_model,
                to_many=True,
                reverse=True
            )
        return one_to_many, many_to_many_reverse

    def save(self, *args, **kwargs):
        self.updated_at = int(time.time())
        if not self.created_at:
            self.created_at = int(time.time())
        return super().save(*args, **kwargs)

    def create_datetime(self):
        return mark_safe(
            datetime.fromtimestamp(
                self.created_at
            ).strftime(MODEL_DATETIME_FORMAT)
        )
    def update_datetime(self):
        return mark_safe(
            datetime.fromtimestamp(
                self.updated_at
            ).strftime(MODEL_DATETIME_FORMAT)
        )


