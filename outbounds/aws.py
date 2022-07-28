import boto3

class AwsS3Client:
    def __init__(self) -> None:
        self.address = " ... "
        self.bucket = " ... "
        self.client: boto3.client = boto3.client(
            "s3",
            aws_access_key_id=" ... ",
            aws_secret_access_key=" ... ",
        )

    def wait_until_exists(
        self, filename: str, delay: int = 5, attempts: int = 2
    ) -> None:
        waiter = self.client.get_waiter("object_exists")
        waiter.wait(
            Bucket=self.bucket,
            Key=filename,
            WaiterConfig={
                "Delay": delay,
                "MaxAttempts": attempts,
            },
        )

    def image_upload(self, image: str, path: str) -> str:
        self.client.put_object(
            Key=path,
            Body=image,
            Bucket=self.bucket,
            ContentType="image/png",
        )
        return f"{self.address}/{path}"

    def delete(self, image_url) -> None:
        filename: str = image_url.replace(f"{self.address}", "")
        self.client.delete_object(
            Bucket=self.bucket,
            Key=filename,
        )
