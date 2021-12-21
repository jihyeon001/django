import uuid
import time
from datetime     import datetime

from django.db                        import models
from django.utils.safestring          import mark_safe
from django.core.validators           import MaxValueValidator
from rest_framework.utils.model_meta  import get_field_info

MAX_UNIX_TIME_STAMP = 2147483647
MODEL_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset() #.filter(is_active=True)

class BaseModel(models.Model):
    """
        This model defines base models that implements common fields
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
        forward_relations, reverse_relations = cls.get_relation_info()

        prefetch_fields = [field for field, _ in reverse_relations.items() \
                                    if not field in excludes]
        prefetch_fields += [field for field, relation_indo in forward_relations.items() \
                                    if not field in excludes and relation_indo.to_many]
        select_fields = [field for field, relation_indo in forward_relations.items() \
                                    if not field in excludes and not relation_indo.to_many]
        if select_fields:
            Model_Objects = Model_Objects.select_related(*select_fields)
        if prefetch_fields:
            Model_Objects = Model_Objects.prefetch_related(*prefetch_fields)
        return Model_Objects

    @classmethod
    def get_relation_info(cls):
        field_info = get_field_info(cls)
        return (
            field_info.forward_relations,
            field_info.reverse_relations
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