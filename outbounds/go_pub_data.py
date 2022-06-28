import json
import os

from requests import get, Response
from abc import ABCMeta, abstractmethod
from types import SimpleNamespace
from typing import Union, List

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

class GoPubDataConfig:
    def __init__(self, config_json: dict) -> None:
        self.BASE_URL = config_json["BASE_URL"]
        self.ENCODED_KEY = config_json["ENCODED_KEY"]
        self.DECODED_KEY = config_json["DECODED_KEY"]


class GoPubDataApiAdapter(metaclass=ABCMeta):
    def __init__(self, apis_json: dict) -> None:

        api: dict = apis_json[self.endpoint]
        self.headers_keys = SimpleNamespace(**api["headers"])
        self.params_keys = SimpleNamespace(**api["params"])
        self.response_keys = SimpleNamespace(**api["response"])
        self.response_data_keys = SimpleNamespace(**api["response_data"])

    @property
    @abstractmethod
    def endpoint(self) -> str:
        pass

    def postprocess(self, datas: list) -> dict:
        return {
            data[self.response_data_keys.svc_id]: {
                key: {"key": kor_key, "value": data[kor_key]}
                for key, kor_key in self.response_data_keys.__dict__.items()
            }
            for data in datas
        }


class GoPubDataClient:
    def __init__(self, config: GoPubDataConfig, adapter: GoPubDataApiAdapter) -> None:
        self.adapter: GoPubDataApiAdapter = adapter
        self.config: GoPubDataConfig = config

        self.url = f"{self.config.BASE_URL}/{self.adapter.endpoint}"
        self.datas, self.result, self.total_count = [], {}, 0

        self.set_request_attrs()

        print(self.adapter.endpoint, " 수집시작")
        self.request()

    def set_request_attrs(self) -> None:

        self.headers = SimpleNamespace(
            **{
                self.adapter.headers_keys.authorization: self.config.ENCODED_KEY,
                self.adapter.headers_keys.accept: "application/json",
            }
        )

        self.params = SimpleNamespace(
            **{
                self.adapter.params_keys.page: 1,
                self.adapter.params_keys.per_page: 1000,
                self.adapter.params_keys.return_type: "JSON",
                self.adapter.params_keys.service_key: self.config.DECODED_KEY,
            }
        )

    def request(self) -> None:
        response: Response = get(
            url=self.url,
            headers=self.headers.__dict__,
            params=self.params.__dict__,
        )

        print(
            getattr(self.params, self.adapter.params_keys.page),
            "페이지 수집 -> ",
            response.status_code,
        )

        responsed_data = json.loads(response.text)
        self.datas += responsed_data[self.adapter.response_keys.data]
        self.recur_or_postprocess(
            total_count=responsed_data[self.adapter.response_keys.total_count]
        )

    def recur_or_postprocess(self, total_count: int) -> None:
        page = getattr(self.params, self.adapter.params_keys.page)
        per_page = getattr(self.params, self.adapter.params_keys.per_page)

        if total_count > (per_page * page):
            setattr(self.params, self.adapter.params_keys.page, page + 1)
            self.request()
        else:
            print(total_count, "개 중 ", len(self.datas), "개 수집완료")
            self.result = self.adapter.postprocess(self.datas)


class GoPubDataService:
    def __init__(
        self,
        config: GoPubDataConfig,
        adapters: List[GoPubDataApiAdapter],
        storage_path: str,
    ) -> None:
        self.config: GoPubDataConfig = config
        self.storage_path = storage_path
        self.adapters = adapters

        self.initial_api_clients()
        self.set_svc_ids()

    def initial_api_clients(self) -> None:
        for adapter in self.adapters:
            setattr(
                self,
                adapter.endpoint + "_client",
                GoPubDataClient(
                    config=self.config,
                    adapter=adapter,
                ),
            )

    def get_api_clients(self) -> List[GoPubDataClient]:
        api_clients = [
            getattr(self, adapter.endpoint + "_client") for adapter in self.adapters
        ]
        return sorted(api_clients, key=lambda x: len(x.result.keys()), reverse=True)

    def set_svc_ids(self):
        ids_list = [client.result.keys() for client in self.get_api_clients()]
        self.svc_ids = list(set([i for ids in ids_list for i in ids]))

    def to_json(self, data: Union[list, dict]) -> None:
        json.dump(
            data,
            open(self.storage_path, mode="w", encoding="utf8"),
            indent=2,
            ensure_ascii=False,
        )

    def merge(self) -> dict:
        base, *others = self.get_api_clients()
        for key in base.result.keys():
            for other in others:
                base.result[key].update(
                    other.result.get(key, {other.adapter.endpoint: {}})
                )
        return base.result
