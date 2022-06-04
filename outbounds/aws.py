import boto3

class AwsS3Client:

    def __init__(self, aws_s3_config: dict) -> None:
        self.client = boto3.client(
            's3',
            aws_access_key_id     = aws_s3_config['ACCESS_ID'],
            aws_secret_access_key = aws_s3_config['ACCESS_SECRET'],
        )
        self.waiter = self.client.get_waiter('object_exists')
        self.waiter_config = {
            'Delay': 5,
            'MaxAttempts': 2
        }
        self.bucket_name = aws_s3_config['BUCKET_NAME']
        self.address = aws_s3_config["ADDRESS"]


    def upload(self, file_object, content_type: str, key: str):
        self.client.upload_fileobj(
            Key       = key,
            Fileobj   = file_object,
            ExtraArgs = {'ContentType': getattr(
                file_object, 'content_type', content_type
            )},
            Bucket    = self.bucket_name
        )
        self._wait_until_exists(key=key)

    def delete(self, image_url):
        key = image_url.replace(f'{self.address}', '')
        self.client.delete_object(
            Bucket = self.bucket_name,
            Key    = key,
        )

    def _wait_until_exists(self, key: str):
        self.waiter.wait(
            Bucket=self.bucket_name,
            Key=key,
            WaiterConfig=self.waiter_config
        )