import json
import os

from requests import get, Response
from abc import ABCMeta, abstractmethod
from types import SimpleNamespace
from typing import Union, List

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


class GoPubDataConfig:
    def __init__(
        self,
        dirname: str,
        filename: str,
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


class GoPubDataClient:
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

        print(self.api.endpoint, " 수집시작")
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

        print(
            getattr(self.params, self.api.params_keys.page),
            "페이지 수집 -> ",
            response.status_code,
        )

        responsed_data = json.loads(response.text)
        self.datas += responsed_data[self.api.response_keys.data]
        self.recur_or_postprocess(
            total_count=responsed_data[self.api.response_keys.total_count]
        )

    def recur_or_postprocess(self, total_count: int) -> None:
        page = getattr(self.params, self.api.params_keys.page)
        per_page = getattr(self.params, self.api.params_keys.per_page)

        if total_count > (per_page * page):
            setattr(self.params, self.api.params_keys.page, page + 1)
            self.request()
        else:
            print(total_count, "개 중 ", len(self.datas), "개 수집완료")
            self.result = self.api.postprocess(self.datas)



