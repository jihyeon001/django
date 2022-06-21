from io import BufferedReader
import boto3
import json

class AwsS3FileObject:
    def __init__(self, reader: BufferedReader, content_type: str, key: str) -> None:
        self.reader: BufferedReader = reader
        self.content_type: str = content_type
        self.key: str = key

class AwsS3Config:

    def __init__(self, path:str) -> None:
        config_file = json.load(open(path, mode='r', encoding='utf8'))
        self.service: str = 's3'
        self.access_id: str = config_file['ACCESS_ID']
        self.access_secret: str = config_file['ACCESS_SECRET']
        self.bucket_name: str = config_file['BUCKET_NAME']
        self.address: str = config_file["ADDRESS"]

class AwsS3ClientAdapter:

    def __init__(self, config: AwsS3Config) -> None:
        self.config: AwsS3Config  = config
        self.client: boto3.client = boto3.client(
            self.config.service,
            aws_access_key_id     = self.config.access_id,
            aws_secret_access_key = self.config.access_secret,
        )

    def get_address(self) -> str:
        return self.config.address

    def get_waiter(self, name: str = 'object_exists'):
        return self.client.get_waiter(name)

    def wait_until_exists(self, key: str, delay: int = 5, attempts: int = 2) -> None:
        waiter = self.get_waiter()
        waiter.wait(
            Bucket=self.config.bucket_name,
            Key=key,
            WaiterConfig={
                'Delay': delay,
                'MaxAttempts': attempts
            }
        )

    def upload(self, file_object: AwsS3FileObject) -> None:
        self.client.upload_fileobj(
            Key       = file_object.key,
            Fileobj   = file_object.reader,
            ExtraArgs = {'ContentType': getattr(
                file_object.reader, 'content_type', file_object.content_type
            )},
            Bucket    = self.config.bucket_name
        )
        self.wait_until_exists(key=file_object.key)

    def delete(self, image_url) -> None:
        key: str = image_url.replace(f'{self.config.address}', '')
        self.client.delete_object(
            Bucket = self.config.bucket_name,
            Key    = key,
        )

