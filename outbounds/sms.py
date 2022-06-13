import hashlib
import hmac
import base64
import time
import json
import requests


class NcloudConfig:

    def __init__(self, json_path:str) -> None:
        config_file = json.load(open(json_path, mode='r', encoding='utf8'))
        self.encoding = config_file['ENCODING']
        self.method = config_file['METHOD']
        self.from_number = config_file['CALLING_NUM']
        self.access_key  = config_file['API_ACCESS_KEY']
        self.secret_key  = bytes(config_file['API_SECRET_KEY'], self.encoding)
        self.uri = config_file['URI']
        self.url = config_file['URL'] + self.uri
        self.success_status_code = config_file['SUCCESS_STATUS_CODE']

class NcloudSimpleEasyNotification:
    
    def __init__(self, content:str, phone:str, config:NcloudConfig) -> None:
        self.content = content
        self.phone = phone.replace('-', '') if '-' in phone else phone
        self.config = config
        self.timestamp = str(int(time.time() * 1000))
    
    def	_get_signature_message(self) -> bytes:
        return bytes('{method} {uri}\n{timestamp}\n{access_key}'.format(
            method=self.config.method, 
            uri=self.config.uri,
            timestamp=self.timestamp,
            access_key=self.config.access_key,
        ), encoding=self.config.encoding)

    def	_get_signature(self) -> bytes:
        return base64.b64encode(hmac.new(
            key=self.config.secret_key, 
            msg=self._get_signature_message(), 
            digestmod=hashlib.sha256
        ).digest())

    def _get_headers(self) -> dict:
        return {
            'Content-Type' : 'application/json; charset=utf-8',
            'x-ncp-iam-access-key' : self.config.access_key,
            'x-ncp-apigw-timestamp' : self.timestamp,
            'x-ncp-apigw-signature-v2' : self._get_signature(),
        }

    def _get_body(self) -> str:
        return json.dumps({
            'type' : 'SMS',
            'from' : self.config.from_number,
            'content' : self.content,
            'messages' : [{'to' : self.phone}],
            'contentType' : 'COMM',
            'countryCode' : '82',
        })

    def send_message(self) -> None:
        response = requests.request(
            self.config.method, 
            self.config.url,
            headers=self._get_headers(),
            data=self._get_body(),
        )

        assert response.status_code == self.config.success_status_code, (
            "{class_name}, "
            "{message} ".format(
                class_name=self.__class__.__name__,
                message=response.text
            )
        )