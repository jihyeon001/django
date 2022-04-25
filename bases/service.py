from .repository         import BaseRepository

class BaseService:
    serializer_class = None

    def __init__(self):
        assert self.serializer_class, f"{self.__class__.__name__} not set serializer class."
        self.repository = BaseRepository(serializer_class=self.serializer_class)

    def check_household_member(self, user_id, household_id):
        return self.repository.check_household_member(user_id, household_id)

    def get_or_create(self, **kwargs):
        return self.repository.get_or_create(**kwargs)

    def get_instance_data(self, instance):
        return self.serializer_class(instance).data

    def run_validation(self, data):
        self.repository.run_validation(data, partial=True)

    def create(self, data):
        return self.repository.create(data)

    def bulk_create(self, data):
        return self.repository.bulk_create(data)

    def partial_update(self, instance, data):
        return self.repository.partial_update(instance, data)

    def destroy(self, instance) -> None:
        self.repository.destroy(instance)

    def get(self, **kwargs):
        return self.repository.get(**kwargs)

    def filter(self, order_by=None, **kwargs):
        return self.repository.filter(order_by, **kwargs)
