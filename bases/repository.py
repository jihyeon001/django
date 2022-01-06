
from commons.exceptions     import (
    AttributeErrorException,
    ObjectDoesNotExistException,
)

class BaseRepository:
    def __init__(self, model_class):
        self.model_class = model_class

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

    def save(self, serializer, many_to_one, many_to_many=None):
        """
            .create() 또는 serializer.save() 방식 대비 약 50%의 속도 개선 
        """
        instance = serializer.save(**many_to_one)
        if many_to_many:
            self._update_many_to_many(instance=instance, many_to_many=many_to_many)
        return instance

    def get_by_model_id(self, model_id):
        try:
            return self.model_class._default_manager.get(id=model_id)
        except self.model_class.DoesNotExist as e:
            raise ObjectDoesNotExistException(message=e)
    
    def filter_by_kwargs(self, **kwargs):
        for field_name in kwargs.keys():
            if not hasattr(self.model_class, field_name):
                raise AttributeErrorException(
                    message=(
                        "{field_name} is not field of '{model_name}' model  ".format(
                            model_name=self.model_class.__name__,
                            field_name=field_name,
                        )
                    )
                )
        data = self._process_nested_dict(data=kwargs)
        return self.model_class.eager_objects().filter(**data)

    def get_eager_objects(self, excludes=()):
        return self.model_class.eager_objects(excludes=excludes)

    def _process_nested_dict(self, data:dict) -> dict:
        _data = dict()
        for key, val in data.items():
            if key in self.many_to_one_info.keys():
                pk = val.get('id', None)
                if pk:
                    _data[key + '_id'] = pk
            elif key in self.many_to_many_info.keys():
                continue
            else:
                _data[key] = val
        return _data