from collections     import OrderedDict
from rest_framework  import serializers
from datetime        import datetime

class BaseTest:
    serializer_class = None
    field_type_map = {
        serializers.BooleanField  : bool,
        serializers.EmailField    : str,
        serializers.UUIDField     : str,
        serializers.CharField     : str,
        serializers.IntegerField  : int,
        serializers.DateTimeField : datetime,
        serializers.URLField      : str,
        serializers.FloatField    : float,
    }

    def __init__(self, service):
        """
            - serializer의 .get_fields() method로 필드 정보
            - 역참조 제외
        """
        assert self.serializer_class, f"{self.__class__.__name__} not set serializer class."
        self.fields = self.serializer_class().get_fields()

    def get_testcases(self) -> list:
        pass

    def get_field_type_class(self, field_name: str):
        """
            각 필드의 type class를 반환
            nested data는 serializer.data의 결과값을 참고
                - many-to-many, reverse일 경우 list
                - many-to-one일 경우 dict
        """
        field = self.fields.get(field_name, None)
        assert field, (
            '{model_name} model has no attribute {field_name}'.format(
                model_name=self.serializer_class.Meta.model.__name__,
                field_name=field_name
            )
        )
        if not issubclass(field.__class__, serializers.Field):
            return list if hasattr(field, 'many') else OrderedDict
        return self.field_type_map[field.__class__]

    def assert_type_test(self, field_name: str, field_value, type_class):
        """
            type class와 비교 테스트
        """
        target_type = type(field_value)
        assert target_type == type_class, (
            "Type Error, {model_name} model {field_name} field "
            "Expected type '{field_type}' but got type {wrong_type}".format(
                model_name=self.serializer_class.Meta.model.__name__,
                field_name=field_name,
                field_type=type_class.__name__,
                wrong_type=target_type
            )
        )
