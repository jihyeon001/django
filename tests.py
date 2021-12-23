from collections     import OrderedDict
from rest_framework  import serializers
from datetime        import datetime

class TestRequest:
    def __init__(self, data):
        self.data = data

class BaseServiceTest:
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
        self.service = service
        self.service_class = self.service.__class__
        self.serializer_class = self.service.serializer.__class__
        self.fields = self.serializer_class().get_fields()

    def test(self):
        pass

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

    def get_serializer_context(self, data: dict):
        """
            serializer의 context에 들어갈 request 반환
        """
        return {'request': TestRequest(data=data)}

    def get_create_testset(self, data: dict):
        serializer = self.serializer_class()
        serializer.context = self.get_serializer_context(data=data)

        service = self.service_class(serializer=serializer)
        created_instance = service.create()
        created_data = self.serializer_class(created_instance).data
        return created_instance, created_data
    
    def get_update_testset(self, data: dict, instance, partial: bool):
        serializer = self.serializer_class()
        serializer.context = self.get_serializer_context(data=data)

        service = self.service_class(serializer=serializer)
        updated_instance = service.update(instance, partial)
        updated_data = self.serializer_class(updated_instance).data
        return updated_instance, updated_data