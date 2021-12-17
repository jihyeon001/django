from collections     import OrderedDict
from rest_framework  import serializers

class TestRequest:
    def __init__(self, data):
        self.data = data

class BaseServiceTest:
    primary_key_name = 'id'
    max_m2m_count = 6
    test_string = '테스트'
    test_integer = 1234
    type_test_data = dict()

    def __init__(self, service):
        '''
            테스트용 랜덤 데이터 생성
            - get_fields 메서드로 필드 정보
            - 역참조 제외
            - 타입 테스트용 데이터를 생성하여 타입 체크 후 반환

            x - 각 필드에 해당하는 랜덤값 생성
        '''
        self.service = service
        self.service_class = self.service.__class__
        self.serializer = service.serializer
        self.serializer_class = self.serializer.__class__

        for key, field in self.serializer.get_fields().items():
            if key == self.primary_key_name:
                type_test_value = self.test_string

            elif isinstance(field, serializers.CharField):
                type_test_value = self.test_string

            elif isinstance(field, serializers.IntegerField):
                if field.max_value:
                    continue
                type_test_value = self.test_integer

            elif 'serializer' in field.__class__.__name__.lower():
                if hasattr(field, 'many') and field.many:
                    type_test_value = [self.test_string, self.test_integer]
                else:
                    type_test_value =  OrderedDict({self.test_string:self.test_integer}.items())
            self.type_test_data[key] = type_test_value
    
    def _get_test_request(self, data):
        return TestRequest(data=data)

    def _type_test(self, source, target):
        model_name = self.serializer_class.Meta.model.__name__
        for key, val in source.items():
            assert type(target[key]) == type(val), f'{model_name}모델 {key}의 타입이 다름'

    def get_create_testset(self, data):
        test_request = self._get_test_request(data=data)
        serializer = self.serializer_class()
        serializer.context['request'] = test_request

        service = self.service_class(serializer=serializer)
        created_instance = service.create()
        created_data = self.serializer_class(created_instance).data

        self._type_test(source=self.type_test_data, target=created_data)
        return created_instance, created_data
    
    def get_update_testset(self, data, instance, partial):
        test_request = self._get_test_request(data=data)
        serializer = self.serializer_class()
        serializer.context['request'] = test_request

        service = self.service_class(serializer=serializer)
        updated_instance = service.update(instance, partial)
        updated_data = self.serializer_class(updated_instance).data

        self._type_test(source=self.type_test_data, target=updated_data)
        return updated_instance, updated_data