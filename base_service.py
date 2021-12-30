from .exceptions    import (
    KeyErrorException, 
    ObjectDoesNotExistException,
)

class BaseService:
    def __init__(self, serializer):
        self.serializer = serializer
        self.model_class = serializer.Meta.model
        self.request = serializer.context.get('request', None)
        self.relation_extraction = RelationExtraction(model_class=self.model_class)

    def _get_validated_serializer(self, data, instance=None, partial=False):
        """
            serializer로 유효성 체크
        """
        serializer = self.serializer.__class__(
            instance=instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return serializer

    def _update_many_to_many(self, instance, many_to_many):
        """
            기존 값과 비교 후
            *arguments 한번에 쿼리를 실행
        """
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
        """
            .create() 또는 serializer.save() 방식 대비 약 50%의 속도 개선 
        """
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
            self._update_many_to_many(instance=instance, many_to_many=many_to_many)
        return instance


class RelationExtraction:
    def __init__(self, model_class):
        self.model_class = model_class
        self.many_to_one, self.many_to_many, self.reverse_relations = self.model_class.get_relation_info()
        
    @staticmethod
    def get_related_instance(related_model_class, nested_data):
        """
            related_model의 instance를 반환
        """
        if not nested_data:
            raise KeyErrorException(message=related_model_class.__name__)
        try:
            return related_model_class._default_manager.get(**nested_data)
        except related_model_class.DoesNotExist as e:
            raise ObjectDoesNotExistException(message=e)

    def _get_many_to_one_instance(self, field_name, nested_data:dict) -> dict:
        """
            many_to_one 인스턴스 반환
        """
        relation_info = self.many_to_one.get(field_name, None)
        assert isinstance(nested_data, dict), (
            "{field_name} of '{model_name}' model "
            "is many-to-one relation field. so, nested data must be dictionary".format(
                model_name=self.model_class.__name__,
                field_name=field_name
            )
        )

        return self.get_related_instance(
            related_model_class=relation_info.related_model,
            nested_data=nested_data
        )

    def _get_many_to_many_instances(self, field_name, nested_datas:list) -> list:
        """
            many_to_many 인스턴스 반환
        """
        relation_info = self.many_to_many.get(field_name, None)
        assert isinstance(nested_datas, list), (
            "{field_name} of '{model_name}' model "
            "is many-to-many relation field. so, nested data must be list".format(
                model_name=self.model_class.__name__,
                field_name=field_name
            )
        )

        return [
            self.get_related_instance(
                related_model_class=relation_info.related_model,
                nested_data=nested_data
            )
        for nested_data in nested_datas]

    def get_field_data(self, data):
        """
            many to many relation 필드 분리
            many to one relation은 key : instance로 변환
        """
        many_to_many = dict()
        many_to_one = dict()
        field = dict()
        for field_name, val in data.items():
            if field_name in self.many_to_one.keys():
                many_to_one[field_name] = self._get_many_to_one_instance(
                    field_name=field_name, 
                    nested_data=val
                )
            elif field_name in self.many_to_many.keys():
                many_to_many[field_name] = self._get_many_to_many_instances(
                    field_name=field_name, 
                    nested_datas=val
                )
            else:
                field[field_name] = val
        return field, many_to_one, many_to_many 