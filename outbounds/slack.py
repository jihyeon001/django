import requests
import json

SLACK: dict

class SlackIncomingWebhooks:
    success_status_code = 200
    url = SLACK['URL']
        
    def request(self, contents):
        payload = {
            'text':f':rotating_light:[{contents}'
        }
        response = requests.post(
            url=self.url,
            data=json.dumps(payload),
            headers={'Content-Type':'application/json'}
        )
        assert response.status_code == self.success_status_code, (
            "{class_name}, "
            "{message} ".format(
                class_name=self.__class__.__name__,
                message=response.text
            )
        )