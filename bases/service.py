from abc import abstractclassmethod
from .repository import Repository


class Service:

    def  __init__(self, repository: Repository) -> None:
        self.repository: Repository = repository

    @abstractclassmethod
    def get(self, **kwargs):
        pass

    @abstractclassmethod
    def filter(self, **kwargs):
        pass
