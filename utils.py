import uuid
import cv2
import numpy
import os
import threading
from .exceptions   import InternalServerErrorException
from .outbounds    import AwsS3Client

THUMBNAIL_WIDTH: int

class AwsS3ImageUploader:
    DEFAULT_CONTENT_TYPE = 'image/jpeg'
    BUFFER_PATH   = '...이미지 파일 경로.../buffer/'
    aws_s3_client = AwsS3Client()

    def __init__(self, image_bytes: bytes, image_key: str):
        self.path = self.BUFFER_PATH + image_key.replace('/', '-')
        self.image_key = image_key
        self.image_bytes = image_bytes

    def _read_image_file(self):
        open(self.path, mode='wb').write(self.image_bytes)
        return open(self.path, mode='rb')

    def upload(self):
        try:
            self.aws_s3_client.upload(
                file_object=self._read_image_file(),
                content_type=self.DEFAULT_CONTENT_TYPE,
                key=self.image_key,
            )
            os.remove(self.path)
        except Exception as e:
            raise InternalServerErrorException(
                message=f'{self.__class__.__name__} {e}'
            )

class ImageResizeUpload:
    THUMBNAIL_IMAGE_KEY_SUFFIX = '-thumbnail'
    SOURCE_IMAGE_KEY_SUFFIX = '-src'

    def __init__(self, directory: str, image):
        url_generator = str(uuid.uuid4())
        self.base_key = f'{directory}/{url_generator}/{url_generator[:8]}'
        self.image = image

        # source image를 binary로 읽고 난후 decode
        encoded_image = numpy.fromstring(self.image.read(), dtype=numpy.uint8)
        self.src_image = cv2.imdecode(encoded_image, cv2.IMREAD_COLOR)

    def _get_thumb_height(self) -> int:
        """
            source image의 크기로 계산된 비율로 thumbnail image의 높이를 산출
        """
        height, width, _ = self.src_image.shape
        ratio = float(height) / float(width)
        return round(ratio * THUMBNAIL_WIDTH)

    def _get_thumbnail_image(self):
        """
            resize image 
        """
        thumb_height = self._get_thumb_height()
        return cv2.resize(self.src_image, dsize=(THUMBNAIL_WIDTH, thumb_height), interpolation=cv2.INTER_LINEAR)


    def _get_decoded_image(self):
        """
            cv2.imdecode()를 거친 image를 반환
        """
        if is_thumbnail:
            return self._get_thumbnail_image()
        return self.src_image


    def _get_image_key(self, is_thumbnail=False):
        """
            S3의 경로를 반환
        """
        if is_thumbnail:
            return self.base_key + self.THUMBNAIL_IMAGE_KEY_SUFFIX
        return self.base_key + self.SOURCE_IMAGE_KEY_SUFFIX


    def _start_upload_thread(self, image_bytes: bytes, image_key: str) -> str:
        """
            image를 s3에 업로드 하고, bucket address를 반환
        """
        image_uploader = AwsS3ImageUploader(image_bytes, image_key)
        upload_thread = threading.Thread(
            target=image_uploader.upload, 
            args=()
        )
        upload_thread.start()
        return image_uploader.aws_s3_client.ADDRESS

    def _get_image_data(self, is_thumbnail=False) -> dict:
        """
            작업 수행 후 image data를 반환
        """
        image_key = self._get_image_key(is_thumbnail=is_thumbnail)
        decoded_image = self._get_decoded_image(is_thumbnail=is_thumbnail)
        height, width, _ = decoded_image.shape
        image_bytes = cv2.imencode('.jpg', decoded_image)[1].tobytes()
        address = self._start_upload_thread(image_bytes=image_bytes, image_key=image_key)

        return {
            'image_url'    : f'{address}/{image_key}',
            'height'       : height,
            'width'        : width,
            'is_thumbnail' : is_thumbnail
        }

    def get_image_datas(self) -> list:
        try:
            return [
                self._get_image_data(), 
                self._get_image_data(is_thumbnail=True)
            ]
        except Exception as e:
            raise InternalServerErrorException(
                message=f'{self.__class__.__name__} {e}'
            )

