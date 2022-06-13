import hashlib
import hmac
import base64
import time
import json
import requests

from abc import ABCMeta, abstractmethod

class NcloudSMSType(metaclass=ABCMeta):

    def __init__(self, content: str, to: str) -> None:
        assert len(content) < self.max_length, "content is too long"
        self.content = content
        self.to = to.replace('-', '') if '-' in to else to

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def max_length(self):
        pass

    def get_body(self) -> dict:
        return {
            'type' : self.name,
            'content' : self.content,
            'messages' : [{'to' : self.to}],
            'contentType' : 'COMM',
            'countryCode' : '82',
        }


class SMS(NcloudSMSType):
    name = 'SMS'
    max_length = 80


class LMS(NcloudSMSType):
    name = 'LMS'
    max_length = 2000

    def __init__(self, content: str, to: str, subject: str) -> None:
        super().__init__(content, to)
        self.subject = subject
    
    def get_body(self) -> dict:
        body = super().get_body()
        body['messages'] = [{
            'to' : self.to,
            'subject' : self.subject,
            'content' : self.content,
        }]
        return body

class MMS(LMS):
    name = 'MMS'
    max_length = 2000

    def __init__(self, content: str, to: str, subject: str, image_name: str, image_body: str) -> None:
        super().__init__(content, to, subject)
        self.image_name = image_name
        self.image_body = image_body

    def get_body(self) -> dict:
        body = super().get_body()
        body['files'] = [{
            'name' : self.image_name,
            'body' : self.image_body,
        }]
        return body

class NcloudSMSConfig:

    def __init__(self, path:str) -> None:
        config_file = json.load(open(path, mode='r', encoding='utf8'))
        self.encoding = config_file['ENCODING']
        self.method = config_file['METHOD']
        self.from_number = config_file['CALLING_NUM']
        self.access_key  = config_file['API_ACCESS_KEY']
        self.secret_key  = bytes(config_file['API_SECRET_KEY'], self.encoding)
        self.uri = config_file['URI']
        self.url = config_file['URL'] + self.uri
        self.success_status_code = config_file['SUCCESS_STATUS_CODE']

class NcloudSimpleEasyNotification:
    
    def __init__(self, sms: NcloudSMSType, config: NcloudSMSConfig) -> None:
        self.config = config
        body: dict = sms.get_body()
        body['from'] = self.config.from_number,
        self.body: str = json.dumps(body)
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

    def send_message(self) -> None:
        response = requests.request(
            self.config.method, 
            self.config.url,
            headers=self._get_headers(),
            data=self.body,
        )

        assert response.status_code == self.config.success_status_code, (
            "{class_name}, "
            "{message} ".format(
                class_name=self.__class__.__name__,
                message=response.text
            )
        )