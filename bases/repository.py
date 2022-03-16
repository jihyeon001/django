from django.db.models.query    import QuerySet
from rest_framework.exceptions import ValidationError

from commons.exceptions     import ObjectDoesNotExistException

FITER_LOOKUP_SEPARATOR: str

class BaseRepository:

    def __init__(self, serializer_class):
        self.serializer_class = serializer_class
        self.model_class = serializer_class().Meta.model

    def _update_many_to_many(self, serializer, instance) -> None:
        for key, ids in serializer.many_to_many_ids.items():
            exists   = set([i.id for i in getattr(instance, key).all()])
            updates  = set(ids)
            addeds   = updates - exists
            deleteds = exists - updates
            if addeds:
                getattr(instance, key).add(*addeds)
            if deleteds:
                getattr(instance, key).remove(*deleteds)

    def run_validation(self, data, instance=None, partial=None, many=False):
        serializer = self.serializer_class(data=data, instance=instance, partial=partial, many=many)
        serializer.is_valid()
        self.raise_exception(serializer)
        return serializer

    def raise_exception(self, serializer) -> None:
        errors = serializer.errors
        if errors:
            errs = {}
            for key, vals in errors.items():
                if isinstance(vals[0], dict):
                    vals = list(vals[0].values())[0]
                errs[key] = {
                    'message':str(vals[0]),
                    'code':vals[0].code,
                }
            raise ValidationError(errs)

    def save(self, serializer) -> dict:
        instance = serializer.save()
        if hasattr(serializer, 'many_to_many_ids'):
            self._update_many_to_many(serializer, instance=instance)
        return instance

    def create(self, data) -> dict:
        serializer = self.run_validation(data=data)
        return self.save(serializer)

    def bulk_create(self, data) -> dict:
        serializer = self.run_validation(data=data, many=True)
        return self.save(serializer)

    def partial_update(self, instance, data) -> dict:
        serializer = self.run_validation(data=data, instance=instance, partial=True)
        return self.save(serializer)

    def destroy(self, instance) -> None:
        instance.delete()

    def get_or_create(self, **kwargs) -> tuple:
        return self.model_class.objects.eager.get_or_create(**kwargs)

    def get(self, **kwargs):
        try:
            return self.model_class.objects.eager.get(**kwargs)
        except self.model_class.DoesNotExist as e:
            raise ObjectDoesNotExistException()
    
    def filter(self, order_by=None, **kwargs) -> QuerySet:
        queryset = self.model_class.objects.eager.filter(**kwargs)

        if order_by:
            if isinstance(order_by, str):
                queryset = queryset.order_by(order_by)
            elif isinstance(order_by, list):
                queryset = queryset.order_by(*order_by)

        return queryset