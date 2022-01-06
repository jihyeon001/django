import requests
import json
from commons.exceptions  import InternalServerErrorException

SLACK: dict

class SlackIncomingWebhooks:
    url = SLACK['URL']
        
    def request(self, contents):
        try:
            payload = {
                'text':f':rotating_light:[{contents}'
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
