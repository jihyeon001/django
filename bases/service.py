from django.db.models.query import QuerySet

from .model      import Model
from .repository import Repository


class Service:

    def  __init__(self, repository: Repository) -> None:
        self.repository: Repository = repository

    def get(self, **kwargs) -> Model:
        self.repository.get(**self.kwargs)

    def filter(self, **kwargs) -> QuerySet:
        self.repository.filter(**kwargs)
