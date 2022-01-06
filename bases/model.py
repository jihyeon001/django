import uuid
import time
from datetime    import datetime
from collections import OrderedDict, namedtuple

from django.db               import models
from django.utils.safestring import mark_safe
from django.core.validators  import MaxValueValidator

MAX_UNIX_TIME_STAMP: int = 2147483647
MODEL_DATETIME_FORMAT : str = '%Y-%m-%d %H:%M:%S'

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
    def eager_objects(cls, excludes=()):
        """
            Relation field를 가져와 eager loading 적용
            - 30% 속도 개선
            - 제외할 필드를 excludes로 전달
        """
        Model_Objects = cls._default_manager
        many_to_one, many_to_many, reverse_relations = cls.get_relation_info()

        prefetch_fields = [field for field, _ in reverse_relations.items() if not field in excludes]
        prefetch_fields += [field for field, _ in many_to_many.items() if not field in excludes]
        select_fields = [field for field, _ in many_to_one.items() if not field in excludes]
        
        if select_fields:
            Model_Objects = Model_Objects.select_related(*select_fields)
        if prefetch_fields:
            Model_Objects = Model_Objects.prefetch_related(*prefetch_fields)
        return Model_Objects

    @classmethod
    def get_relation_info(cls):
        opts = cls._meta.concrete_model._meta
        many_to_one, many_to_many = _get_forward_relationships(opts)
        return (
            many_to_one,
            many_to_many,
            _get_reverse_relationships(opts)
        )

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

RelationInfo = namedtuple('RelationInfo', [
    'field',
    'related_model',
    'to_many',
    'reverse'
])

def _get_forward_relationships(opts) -> tuple:
    """
        forward relation field의 정보를 RelationInfo에 담아
        many-to-one과 many-to-many를 분리하여 OrderedDict으로 반환
    """
    many_to_one_relations = OrderedDict()
    for field in [field for field in opts.fields if field.serialize and field.remote_field]:
        many_to_one_relations[field.name] = RelationInfo(
            field=field,
            related_model=field.remote_field.model,
            to_many=False,
            reverse=False
        )
    # Deal with forward many-to-many relationships.
    many_to_many_relations = OrderedDict()
    for field in [field for field in opts.many_to_many if field.serialize]:
        many_to_many_relations[field.name] = RelationInfo(
            field=field,
            related_model=field.remote_field.model,
            to_many=True,
            reverse=False
        )
    return many_to_one_relations, many_to_many_relations

def _get_reverse_relationships(opts) -> OrderedDict:
    """
        reverse relation field의 정보를 RelationInfo에 담아 OrderedDict으로 반환
    """
    reverse_relations = OrderedDict()
    all_related_objects = [r for r in opts.related_objects if not r.field.many_to_many]
    for relation in all_related_objects:
        accessor_name = relation.get_accessor_name()
        reverse_relations[accessor_name] = RelationInfo(
            field=None,
            related_model=relation.related_model,
            to_many=relation.field.remote_field.multiple,
            reverse=True
        )
    # Deal with reverse many-to-many relationships.
    all_related_many_to_many_objects = [r for r in opts.related_objects if r.field.many_to_many]
    for relation in all_related_many_to_many_objects:
        accessor_name = relation.get_accessor_name()
        reverse_relations[accessor_name] = RelationInfo(
            field=None,
            related_model=relation.related_model,
            to_many=True,
            reverse=True
        )
    return reverse_relations