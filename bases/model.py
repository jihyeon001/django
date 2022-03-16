import time
from datetime import datetime
from collections import OrderedDict, namedtuple

from django.db import models
from django.utils.safestring import mark_safe
from django.core.validators import MaxValueValidator


MAX_UNIX_TIME_STAMP = 2147483647
MODEL_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


RelationInfo = namedtuple('RelationInfo', [
    'field',
    'related_model',
    'to_many',
    'reverse'
])


class BaseModelManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset()  # .filter(active=True)

    @property
    def eager(self):
        """
            eager loading using relation field.
        """
        Model_Objects = self
        _m2os, _m2ms, _reverse_names = self.model.get_relation_info()

        select_fields = list(_m2os.keys())
        prefetch_fields = list(_m2ms.keys()) + _reverse_names

        if select_fields:
            Model_Objects = Model_Objects.select_related(*select_fields)
        if prefetch_fields:
            Model_Objects = Model_Objects.prefetch_related(*prefetch_fields)
        return Model_Objects


class BaseModel(models.Model):
    """
        This model defines base models that implements common fields
    """
    id = models.BigAutoField(
        editable=False,
        primary_key=True,
        serialize=False,
        verbose_name='ID'
    )
    objects = BaseModelManager()
    is_active = models.BooleanField(default=True)
    created_at = models.PositiveIntegerField(
        default=0,
        validators=[
            MaxValueValidator(MAX_UNIX_TIME_STAMP)
        ]
    )
    updated_at = models.PositiveIntegerField(
        default=0,
        validators=[
            MaxValueValidator(MAX_UNIX_TIME_STAMP)
        ]
    )

    class Meta:
        abstract = True

    @classmethod
    def get_relation_info(cls):
        """
            set a 'RelationInfo' of all forward fields and
            a list of all accessor name of reverse relationship
            on the model and its parents.
        """
        opts = cls._meta.concrete_model._meta
        _m2os, _m2ms, _reverse_names = OrderedDict(), OrderedDict(), list()
        for field in opts.fields:
            if field.serialize and field.remote_field:
                _m2os[field.name] = RelationInfo(
                    field=field,
                    related_model=field.remote_field.model,
                    to_many=False, reverse=False)

        for field in [field for field in opts.many_to_many if field.serialize]:
            _m2ms[field.name] = RelationInfo(
                field=field,
                related_model=field.remote_field.model,
                to_many=True, reverse=False)

        for relation in opts.related_objects:
            accessor_name = relation.get_accessor_name()
            # relation.field.many_to_many
            if not accessor_name in _reverse_names:
                _reverse_names.append(accessor_name)

        return _m2os, _m2ms, _reverse_names

    def save(self, *args, **kwargs):
        self.updated_at = int(time.time())
        if not self.created_at:
            self.created_at = int(time.time())
        return super().save(*args, **kwargs)

    def create_datetime(self):
        return self._get_mark_safe(self.get_datetime_fromtimestamp(self.created_at))

    def update_datetime(self):
        return self._get_mark_safe(self.get_datetime_fromtimestamp(self.updated_at))

    def _get_mark_safe(self, data):
        return mark_safe(data)

    def get_datetime_fromtimestamp(self, field):
        assert isinstance(field, int), f"field must be 'int'"
        return datetime.fromtimestamp(field).strftime(MODEL_DATETIME_FORMAT)
