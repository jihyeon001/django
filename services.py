from .exceptions        import KeyErrorException, ObjectDoesNotExistException

class BaseService:
    def __init__(self, serializer):
        self.serializer = serializer
        self.model_class = serializer.Meta.model
        self.request = serializer.context.get('request', None)
        self.relation_extraction = RelationExtraction(serializer=serializer)

    def _get_validated_serializer(self, data, instance=None, partial=False):
        serializer = self.serializer.__class__(
            instance=instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return serializer

    def _update_many_to_many(self, instance, many_to_many):
        for key, m2m_instances in many_to_many.items():
            exists   = set(getattr(instance, key).all())
            updates  = set(m2m_instances)
            addeds   = updates - exists
            deleteds = exists - updates
            if addeds:
                getattr(instance, key).add(*addeds)
            if deleteds:
                getattr(instance, key).remove(*deleteds)

    def create(self):
        # 50ms
        field, many_to_one, many_to_many = self.relation_extraction.get_field_data(data=self.request.data)
        serializer = self._get_validated_serializer(data=field)
        instance = serializer.save(**many_to_one)
        if many_to_many:
            self._update_many_to_many(instance=instance, many_to_many=many_to_many)
        return instance

    def update(self, instance, partial=False):
        field, many_to_one, many_to_many = self.relation_extraction.get_field_data(data=self.request.data)
        if field or many_to_one:
            serializer = self._get_validated_serializer(
                data=field, instance=instance, partial=partial)
            serializer.save(**many_to_one)
        if many_to_many:
            self._update_many_to_many(instance=instance, m2m_data=many_to_many)
        return instance

class RelationExtraction:
    def __init__(self, serializer):
        '''
            참조관계 추출 (2ms 소요)
            -   rest_framework.utils.model_meta.get_field_info()의 경우
                필드 정보와 Relation 필드의 Model까지만 제공되고
                속도도 두배정도 소요 되어서 패스   
        '''
        self.serializer = serializer
        # relation serializer 클래스 추출
        self.nested_serializer = dict()
        for key, field in self.serializer.get_fields().items():
            if 'serializer' in field.__class__.__name__.lower():
                if hasattr(field, 'many') and field.many:
                    self.nested_serializer[key] = field.child.__class__
                else:
                    self.nested_serializer[key] = field.__class__

    @staticmethod
    def get_relation_instance(serializer_class, dictionary):
        relation_id = dictionary.pop('id', None)
        relation_model_class = serializer_class.Meta.model
        if relation_id:
            try:
                return relation_model_class._default_manager.get(id=relation_id)
            except relation_model_class.DoesNotExist as e:
                raise ObjectDoesNotExistException(message=e)
        else:
            raise KeyErrorException(message=relation_model_class.__name__)

    def _get_many_to_one_instance(self, key, val):
        '''
            many_to_one 인스턴스 반환
        '''
        serializer = self.nested_serializer[key]
        return self.get_relation_instance(serializer_class=serializer, dictionary=val)

    def _get_many_to_many_instances(self, key, val) -> list:
        '''
            many_to_many 인스턴스 반환
        '''
        serializer = self.nested_serializer[key]
        return [
            self.get_relation_instance(serializer_class=serializer, dictionary=nested_val)
        for nested_val in val]

    def get_field_data(self, data):
        '''
            many to many relation 필드 분리
            many to one relation은 key : instance로 변환
        '''
        many_to_many = dict()
        many_to_one = dict()
        field = dict()

        for key, val in data.items():
            if isinstance(val, dict):
                many_to_one[key] = self._get_many_to_one_instance(key=key, val=val)
            elif isinstance(val, list):
                many_to_many[key] = self._get_many_to_many_instances(key=key, val=val)
            else:
                field[key] = val
        return field, many_to_one, many_to_many 