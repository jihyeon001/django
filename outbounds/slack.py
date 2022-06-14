import requests
import json

class SlackConfig:

    def __init__(self, path: str) -> None:
        config_file = json.load(open(path, mode='r', encoding='utf8'))
        self.url = config_file['URL']
        self.headers = {'Content-Type': 'application/json'}
        self.emojis = config_file['EMOJIS']

class SlackIncomingWebhooks:

    def __init__(self, config: SlackConfig, comment: str, emoji_name: str = 'rotating_light') -> None:
        self.config = config
        emoji = self.config.emojis.get(emoji_name, ':rotating_light:')
        self.payload = {
            'text': f'{emoji}{comment}'
        }

    def request(self) -> None:
        response = requests.post(
            url=self.config.url,
            data=json.dumps(self.payload),
            headers=self.config.headers
        )
        assert response.status_code == self.success_status_code, (
            "{class_name}, "
            "{message} ".format(
                class_name=self.__class__.__name__,
                message=response.text
            )
        )