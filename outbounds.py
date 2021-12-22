import requests
import threading
import json
from .exceptions  import InternalServerErrorException

SLACK = {}

class SlackIncomingWebhooks(threading.Thread): 
    url = SLACK['URL']

    def __init__(self, contents: str):
        self.contents = contents
        threading.Thread.__init__(self)

    def run(self):
        """
            비동기 처리
        """
        try:
            payload = {
                'text':f':rotating_light:[{self.contents}'
            }
            requests.post(
                url=self.url,
                data=json.dumps(payload),
                headers={'Content-Type':'application/json'}
            )
        except Exception as e:
            raise InternalServerErrorException(
                message=f'{self.__class__.__name__} {e}'
            )