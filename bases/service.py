from commons.exceptions     import ObjectDoesNotExistException

class RelationExtraction:
    def __init__(self, many_to_one_info, many_to_many_info):
        self.many_to_one_info = many_to_one_info
        self.many_to_many_info = many_to_many_info

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
        relation_info = self.many_to_one_info.get(field_name, None)
        assert isinstance(nested_data, dict), (
            f"'{field_name}' field "
            "is many-to-one relation field. "
            "so, nested data must be dictionary"
        )

        return self.get_related_instance(
            related_model_class=relation_info.related_model,
            nested_data=nested_data
        )

    def _get_many_to_many_instances(self, field_name, nested_datas:list) -> list:
        """
            many_to_many 인스턴스 반환
        """
        relation_info = self.many_to_many_info.get(field_name, None)
        assert isinstance(nested_datas, list), (
            f"'{field_name}' field "
            "is many-to-many relation field. "
            "so, nested data must be list"
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
            if field_name in self.many_to_one_info.keys():
                many_to_one[field_name] = self._get_many_to_one_instance(
                    field_name=field_name, 
                    nested_data=val
                )
            elif field_name in self.many_to_many_info.keys():
                many_to_many[field_name] = self._get_many_to_many_instances(
                    field_name=field_name, 
                    nested_datas=val
                )
            else:
                field[field_name] = val
        return field, many_to_one, many_to_many 


class BaseService:
    repository_class = None

    def __init__(self):
        assert self.repository_class, f"{self.__class__.__name__} not set repository class."
        
        self.repository = self.repository_class
        if not hasattr(self.repository, 'field_names'):
            self.repository = self.repository()

        self.field_names = self.repository.field_names
        self.has_user_foreign_key = self.repository.has_user_foreign_key
        self.relation_extraction = RelationExtraction(
            many_to_one_info=self.repository.many_to_one_info, 
            many_to_many_info=self.repository.many_to_many_info,
        )

    def _get_validated_serializer(self, instance=None, partial=False):
        """
            serializer로 유효성 체크
        """

        assert self.field, "field data is empty. must execute set_data() method."
        serializer = self.serializer_class(
            instance=instance, data=self.field, partial=partial)
        serializer.is_valid(raise_exception=True)
        return serializer

    def set_field_data(self, data):
        """
            must be action before update, create method
        """
        (
            self.field,
            self.many_to_one, 
            self.many_to_many
        ) = self.relation_extraction.get_field_data(data=data)

    def set_user_foreign_key(self, user):
        if self.has_user_foreign_key:
            self.many_to_one['user'] = user

    def get_eager_objects(self):
        return self.repository.get_eager_objects()

    def get(self, **kwargs):
        return self.repository.get(**kwargs)

    def filter(self, **kwargs):
        return self.repository.filter(**kwargs)

    def exists(self, **kwargs):
        return self.repository.exists(**kwargs)

    def update(self, instance, partial=False):
        serializer = self._get_validated_serializer(instance=instance, partial=partial)
        return self.repository.save(serializer, self.many_to_one, self.many_to_many)

    def create(self):
        serializer = self._get_validated_serializer()
        return self.repository.save(serializer, self.many_to_one, self.many_to_many)

        


