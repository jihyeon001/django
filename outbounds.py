import requests
import threading
import json
import boto3
from .exceptions  import InternalServerErrorException

SLACK = {}
AWS_S3 = {}
class SlackIncomingWebhooks(threading.Thread): 
    url = SLACK['URL']

    def __init__(self, contents: str):
        self.contents = contents
        threading.Thread.__init__(self)

    def run(self):
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

class AwsS3Client:
    s3_client = boto3.client(
        's3',
        aws_access_key_id     = AWS_S3['ACCESS_ID'],
        aws_secret_access_key = AWS_S3['ACCESS_SECRET'],
    )
    bucket  = AWS_S3['BUCKET_NAME']
    address = AWS_S3["ADDRESS"]

    def upload(self, file_object, content_type: str, key: str):
        try:
            self.s3_client.upload_fileobj(
                Key       = key,
                Fileobj   = file_object,
                ExtraArgs = {'ContentType': getattr(
                    file_object, 'content_type', content_type
                )},
                Bucket    = self.bucket
            )
        except Exception as e:
            raise InternalServerErrorException(
                message=f'{self.__class__.__name__} {e}'
            )

    def delete(self, image_url):
        try:
            key = image_url.replace(f'{self.address}', '')
            self.s3_client.delete_object(
                Bucket = self.bucket,
                Key    = key,
            )
        except Exception as e:
            raise InternalServerErrorException(
                message=f'{self.__class__.__name__} {e}'
            )
