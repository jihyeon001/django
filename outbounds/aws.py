import boto3

AWS_S3: dict

class AwsS3Client:
    client = boto3.client(
        's3',
        aws_access_key_id     = AWS_S3['ACCESS_ID'],
        aws_secret_access_key = AWS_S3['ACCESS_SECRET'],
    )
    waiter = client.get_waiter('object_exists')
    WAITER_COFIG = {
        'Delay': 5,
        'MaxAttempts': 2
    }

    BUCKET_NAME  = AWS_S3['BUCKET_NAME']
    ADDRESS = AWS_S3["ADDRESS"]
    def upload(self, file_object, content_type: str, key: str):
        self.client.upload_fileobj(
            Key       = key,
            Fileobj   = file_object,
            ExtraArgs = {'ContentType': getattr(
                file_object, 'content_type', content_type
            )},
            Bucket    = self.BUCKET_NAME
        )
        self._wait_until_exists(key=key)

    def delete(self, image_url):
        key = image_url.replace(f'{self.ADDRESS}', '')
        self.client.delete_object(
            Bucket = self.BUCKET_NAME,
            Key    = key,
        )

    def _wait_until_exists(self, key: str):
        self.waiter.wait(
            Bucket=self.BUCKET_NAME,
            Key=key,
            WaiterConfig=self.WAITER_COFIG
        )