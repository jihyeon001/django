from rest_framework            import serializers
from rest_framework.exceptions import ValidationError

from collections import OrderedDict
from collections.abc import Mapping
from rest_framework.settings import api_settings
from rest_framework.fields import SkipField
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.fields import get_error_detail, set_value, empty

PRIMARY_KEY_NAME: str

class ModelSerializer(serializers.ModelSerializer):
    many_to_many_ids = {}
    many_to_one_info = OrderedDict()
    many_to_many_info = OrderedDict()

    def __init__(self, *args, **kwargs):
        
        assert hasattr(self.Meta, 'model'), f'{self.__class__.__name__}'

        self.many_to_one_info, self.many_to_many_info, _ = self.Meta.model.get_relation_info()
        self.default_error_messages['notfound'] = '{model_name} object does not exist.'
        super().__init__(*args, **kwargs)

    @staticmethod
    def get_related_instance(related_model, pk_value):
        """
        return related model instance
        """
        try:
            return related_model._default_manager.get(**{PRIMARY_KEY_NAME:pk_value})
        except related_model.DoesNotExist:
            raise ValidationError()

    def _set_many_to_one(self, field, primitive_value):
        """
        many-to-one relation field
        change field_id to model instance
        """
        field_name = field.source_attrs[0]
        field_info = self.many_to_one_info.get(field_name, None)
        field.source_attrs = [field_name]
       
        try:
            related_model = field_info.related_model
            validated_value = self.get_related_instance(related_model, primitive_value)
        except ValidationError:
            detail = self.error_messages['notfound'].format(model_name=related_model.__name__)
            raise ValidationError(detail=detail, code='notfound')
        return field, validated_value

    def _set_many_to_many_ids(self, field, primitive_value):
        """
        many-to-many relation field
        remove it from the data and then 
        append many_to_many_ids which is serializer member variable
        """
        field_name = field.source_attrs[0]

        assert isinstance(primitive_value, list), (
            f"{field_name} which is many-to-many relation must be list"
        )

        field_info = self.many_to_many_info.get(field_name, None)

        error_values = list()
        related_model = field_info.related_model
        many_to_many_ids = []
        for pk in primitive_value:
            try:
                self.get_related_instance(related_model, pk)
                many_to_many_ids.append(pk)
            except ValidationError:
                error_values.append(str(pk))

        self.many_to_many_ids[field_name] = many_to_many_ids
        if error_values:
            detail = self.error_messages['notfound'].format(model_name=related_model.__name__)
            raise ValidationError(detail=detail, code='notfound')


    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            message = self.error_messages['invalid'].format(
                datatype=type(data).__name__
            )
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            }, code='invalid')

        ret = OrderedDict()
        errors = OrderedDict()
        fields = self._writable_fields

        for field in fields:
            validate_method = getattr(self, 'validate_' + field.field_name, None)
            primitive_value = field.get_value(data)

            try:
                if field.source_attrs[0] in self.many_to_many_info and primitive_value is not empty:
                    self._set_many_to_many_ids(field, primitive_value)
                    continue

                validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)

                if field.source_attrs[0] in self.many_to_one_info:
                    field, validated_value = self._set_many_to_one(field, primitive_value)

            except ValidationError as exc:
                errors[field.field_name] = exc.detail
            except DjangoValidationError as exc:
                errors[field.field_name] = get_error_detail(exc)
            except SkipField:
                pass
            else:
                set_value(ret, field.source_attrs, validated_value)
        if errors:
            raise ValidationError(errors)

        return ret