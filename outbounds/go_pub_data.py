import json
import os

from requests import get, Response
from abc import ABCMeta, abstractmethod
from types import SimpleNamespace
from typing import Union

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

class GoPubDataConfig:
    def __init__(
        self,
        dirname: str,
        filename: str,
        storage_dirname: str,
        response_key_filename: str,
    ) -> None:
        config_file = json.load(
            open(f"{PACKAGE_DIR}/{dirname}/{filename}", mode="r", encoding="utf8")
        )
        self.base_url = config_file["BASE_URL"]
        self.encoded_key = config_file["ENCODED_KEY"]
        self.decoded_key = config_file["DECODED_KEY"]
        self.default_headers = SimpleNamespace(**config_file["headers"])
        self.default_params = SimpleNamespace(**config_file["params"])
        self.storage_directory = f"{PACKAGE_DIR}/{storage_dirname}"
        self.key_info_path = f"{PACKAGE_DIR}/{dirname}/{response_key_filename}"


class GoPubDataApi(metaclass=ABCMeta):
    def __init__(self, key_info_path: str) -> None:
        key_info = json.load(open(key_info_path, mode="r", encoding="utf8"))[
            self.endpoint
        ]
        self.headers_keys = SimpleNamespace(**key_info["headers"])
        self.params_keys = SimpleNamespace(**key_info["params"])
        self.response_keys = SimpleNamespace(**key_info["response"])
        self.response_data_keys = SimpleNamespace(**key_info["response_data"])

    @property
    @abstractmethod
    def filename(self) -> str:
        pass

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


class GoPubDataService:
    def __init__(self, config: GoPubDataConfig, api_class: GoPubDataApi) -> None:
        self.api: GoPubDataApi = api_class(key_info_path=config.key_info_path)
        self.config: GoPubDataConfig = config

        self.url = f"{self.config.base_url}/{self.api.endpoint}"
        self.datas, self.result, self.total_count = [], {}, 0

        self.set_request_attrs(
            "params", defaluts=self.config.default_params, keys=self.api.params_keys
        )

        self.set_request_attrs(
            "headers", defaluts=self.config.default_headers, keys=self.api.headers_keys
        )
        self.request()

    def set_request_attrs(
        self, name: str, defaluts: SimpleNamespace, keys: SimpleNamespace
    ) -> None:
        setattr(
            self,
            name,
            SimpleNamespace(
                **{
                    key: getattr(defaluts, key)
                    for key in keys.__dict__.values()
                    if getattr(defaluts, key, None) is not None
                }
            ),
        )

    def request(self) -> None:
        response: Response = get(
            url=self.url,
            headers=self.headers.__dict__,
            params=self.params.__dict__,
        )

        responsed_data = json.loads(response.text)
        self.datas += responsed_data[self.api.response_keys.data]
        self.recur_or_quit(
            total_count=responsed_data[self.api.response_keys.total_count]
        )

    def recur_or_quit(self, total_count: int) -> None:
        page = getattr(self.params, self.api.params_keys.page)
        per_page = getattr(self.params, self.api.params_keys.per_page)

        if total_count > (per_page * page):
            setattr(self.params, self.api.params_keys.page, page + 1)
            self.request()
        else:
            self.result = self.api.postprocess(self.datas)

    def to_json(self, path: str, data: Union[list, dict]) -> None:
        json.dump(
            data, open(path, mode="w", encoding="utf8"), indent=2, ensure_ascii=False
        )

    def merge(self, details: dict, conditions: dict) -> dict:
        return {
            key: {**val, **details[key], **conditions.get(key, {"conditions": {}})}
            for key, val in self.result.items()
        }
