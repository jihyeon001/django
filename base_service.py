from .exceptions     import ObjectDoesNotExistException

class RelationExtraction:
    def __init__(self, model_class):
        self.model_class = model_class
        self.many_to_one, self.many_to_many, self.reverse_relations = self.model_class.get_relation_info()

    @staticmethod
    def get_related_instance(related_model_class, nested_data):
        """
            rest_framework.utils.model_meta.get_field_info()이 적용된
            basemodel의 get_relation_info를 활용 하여
            related_model의 instance를 반환
        """
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


class BaseService:
    def __init__(self, user, repository):
        self.user = user
        self.repository = repository
        self.model_class = self.repository.model_class
        self.relation_extraction = RelationExtraction(model_class=self.model_class)

    def _get_validated_serializer(self, data, instance=None, partial=False):
        """
            serializer로 유효성 체크
        """
        serializer = self.serializer_class(
            instance=instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return serializer

    def get_by_model_id(self, model_id):
        return self.repository.get_by_model_id(model_id=model_id)

    def get_eager_objects(self):
        return self.repository.get_eager_objects()

    def filter_by_kwargs(self, **kwargs):
        return self.repository.filter_by_kwargs(**kwargs)

    def update(self, instance, data, partial=False):
        field, many_to_one, many_to_many = self.relation_extraction.get_field_data(data=data)
        serializer = self._get_validated_serializer(
            instance=instance, data=field, partial=partial)
        return self.repository.save(serializer, many_to_one, many_to_many)

    def create(self, data):
        field, many_to_one, many_to_many = self.relation_extraction.get_field_data(data=data)
        serializer = self._get_validated_serializer(data=field)
        return self.repository.save(serializer, many_to_one, many_to_many)

        


