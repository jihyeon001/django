import boto3
from commons.exceptions  import InternalServerErrorException


AWS_S3: dict

class AwsS3Client:
    s3_client = boto3.client(
        's3',
        aws_access_key_id     = AWS_S3['ACCESS_ID'],
        aws_secret_access_key = AWS_S3['ACCESS_SECRET'],
    )
    BUCKET_NAME  = AWS_S3['BUCKET_NAME']
    ADDRESS = AWS_S3["ADDRESS"]

    def upload(self, file_object, content_type: str, key: str):
        try:
            self.s3_client.upload_fileobj(
                Key       = key,
                Fileobj   = file_object,
                ExtraArgs = {'ContentType': getattr(
                    file_object, 'content_type', content_type
                )},
                Bucket    = self.BUCKET_NAME
            )
        except Exception as e:
            raise InternalServerErrorException(
                message=f'{self.__class__.__name__} {e}'
            )

    def delete(self, image_url):
        try:
            key = image_url.replace(f'{self.ADDRESS}', '')
            self.s3_client.delete_object(
                Bucket = self.BUCKET_NAME,
                Key    = key,
            )
        except Exception as e:
            raise InternalServerErrorException(
                message=f'{self.__class__.__name__} {e}'
            )