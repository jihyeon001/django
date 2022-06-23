import json

from requests import get, Response
from abc import ABCMeta, abstractmethod
from types import SimpleNamespace

class GoPubDataConfig:
    
    def __init__(self, path: str) -> None:
        config_file = json.load(open(path, mode='r', encoding='utf8'))
        self.base_url = config_file['BASE_URL']
        self.encoded_key = config_file['ENCODED_KEY']
        self.decoded_key = config_file['DECODED_KEY']
        self.default_headers = SimpleNamespace(**config_file['headers'])
        self.default_params = SimpleNamespace(**config_file['params'])
        
class GoPubDataApiInfo(metaclass=ABCMeta):

    @property
    @abstractmethod
    def endpoint(self) -> str:
        pass

    @property
    @abstractmethod
    def response_data_keys(self) -> SimpleNamespace:
        pass

    @property
    def headers_keys(self) -> SimpleNamespace:
        return SimpleNamespace(
            authorization="Authorization",
            accept="accept",
        )

    @property
    def params_keys(self) -> SimpleNamespace:
        return SimpleNamespace(
            page="page",
            per="perPage",
            type="returnType",
            key="serviceKey",
            svc_id="cond[SVC_ID::EQ]",
        )

    @property
    def response_keys(self) -> SimpleNamespace:
        return SimpleNamespace(
            page="page", 
            per="perPage", 
            total_count="totalCount", 
            current_count="currentCount", 
            match_count="matchCount", 
            data="data"
        )

class GoPubDataService:
    def get(self, url: str, headers: dict, params: dict) -> Response:        
        return get(
            url=url,
            headers=headers,
            params=params
        )

    def to_dict(self, response: Response) -> dict:
        return json.loads(response.text)

    def to_json(self, path: str, data: dict) -> None:
        json.dump(
            data, 
            open(path, mode='w', encoding='utf8'), 
            indent=2, 
            ensure_ascii=False
        )