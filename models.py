import uuid
import time
from datetime     import datetime
from .exceptions  import KeyErrorException

from django.db                      import models
from django.utils.safestring        import mark_safe
from django.contrib.auth.base_user  import BaseUserManager
from django.core.validators         import MaxValueValidator

ADMIN = {}
MAX_UNIX_TIME_STAMP = 2147483647

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
        return super().get_queryset() #.filter(is_active=True)

class BaseModel(models.Model):
    """
        This model defines base models that implements common fields
    """
    objects         = BaseModelManager()
    id              = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    created_at      = models.IntegerField(default=0, validators=[MaxValueValidator(MAX_UNIX_TIME_STAMP)])
    updated_at      = models.IntegerField(default=0, validators=[MaxValueValidator(MAX_UNIX_TIME_STAMP)])
    
    MANY_TO_ONE_RELATIONS  = tuple()
    ONE_TO_ONE_RELATIONS   = tuple()
    ONE_TO_MANY_RELATIONS  = tuple()
    MANY_TO_MANY_RELATIONS = tuple()
    class Meta:
        abstract=True

    @classmethod
    def get_model_objects(cls, excludes=()):
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
        return mark_safe(datetime.fromtimestamp(self.created_at).strftime('%Y-%m-%d %H:%M:%S'))
    def update_datetime(self):
        return mark_safe(datetime.fromtimestamp(self.updated_at).strftime('%Y-%m-%d %H:%M:%S'))
