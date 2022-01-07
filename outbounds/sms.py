import hashlib
import hmac
import base64
import time
import requests

NAVER_SMS_KEY : dict
UTF8_ENCODING = 'UTF-8'
POST_METHOD = 'POST'

class NaverCloudSimpleEasyNotification:
    success_status_code = 202
    timestamp   = str(int(time.time() * 1000))
    from_number = NAVER_SMS_KEY['CALLING_NUM']
    access_key  = NAVER_SMS_KEY['API_ACCESS_KEY']
    secret_key  = bytes(NAVER_SMS_KEY['API_SECRET_KEY'], UTF8_ENCODING)
    uri = NAVER_SMS_KEY['URI']
    url = NAVER_SMS_KEY['URL']

    def __init__(self, auth_number, phone):
        self.auth_number = auth_number
        self.phone = phone
    
    def _get_signature_message(self):
        return bytes(
            (
                '{method} '
                '{uri}\n'
                '{timestamp}\n'
                '{access_key}'.format(
                    method=POST_METHOD,
                    uri=self.uri,
                    timestamp=self.timestamp,
                    access_key=self.access_key,
                )
            ), encoding=UTF8_ENCODING
        )

    def	_get_signature(self):
        message = self._get_signature_message()
        return base64.b64encode(
            hmac.new(
                self.secret_key, 
                message, 
                digestmod=hashlib.sha256
            ).digest()
        )

    def _get_sms_headers(self):
        return {
            'Content-Type'             : 'application/json; charset=utf-8',
            'x-ncp-apigw-timestamp'    : self.timestamp,
            'x-ncp-iam-access-key'     : self.access_key,
            'x-ncp-apigw-signature-v2' : self._get_signature(),
        }

    def _get_sms_body(self):
        return {
            'type'        : 'SMS',
            'contentType' : 'COMM',
            'countryCode' : '82',
            'from'        : self.from_number,
            'subject'     : '인증문자',
            'content'     : f'인증번호 : {self.auth_number}',
            'messages'    : [{'to' : f'{self.phone}'}]
        }

    def sms(self):
        response = requests.request(
            method=POST_METHOD,
            url=self.url,
            headers=self._get_sms_headers(),
            data=self._get_sms_body(),
        )
        assert response.status_code == self.success_status_code, (
            "{class_name}, "
            "{message} ".format(
                class_name=self.__class__.__name__,
                message=response.text
            )
        )