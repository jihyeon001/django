import uuid
import cv2
import numpy
import os
import threading
from dataclasses     import dataclass
from typing          import List

from .exceptions     import InternalServerErrorException
from outbounds.aws   import AwsS3Client

THUMBNAIL_WIDTH: int

@dataclass
class ImageDto:
    key: str
    byte: bytes
    height: int
    width: int
    is_thumbnail: bool
    url: str = None

class AwsS3ImageUploader:
    DEFAULT_CONTENT_TYPE = 'image/jpeg'
    BUFFER_PATH   = '...이미지 파일 경로.../buffer/'

    def __init__(self, aws_s3_client: AwsS3Client, image_bytes: bytes, image_key: str):
        self.aws_s3_client = aws_s3_client
        self.path = self.BUFFER_PATH + image_key.replace('/', '-')
        self.image_key = image_key
        self.image_bytes = image_bytes

    def _read_image_file(self):
        open(self.path, mode='wb').write(self.image_bytes)
        return open(self.path, mode='rb')

    def upload(self):
        file_object = self._read_image_file()
        assert os.path.exists(self.path) or file_object, (
            "{class_name}, "
            "{image_key} file dose not exist".format(
                class_name=self.__class__.__name__,
                image_key=self.image_key,
            )
        )

        self.aws_s3_client.upload(
            file_object=file_object,
            content_type=self.DEFAULT_CONTENT_TYPE,
            key=self.image_key,
        )
        os.remove(self.path)


class ImageResizeUpload:
    THUMBNAIL_IMAGE_KEY_SUFFIX = '-thumbnail'
    SOURCE_IMAGE_KEY_SUFFIX = '-src'

    def __init__(self, path: str, image):
        url_generator = str(uuid.uuid4())
        self.base_key = f'{path}/{url_generator}/{url_generator[:8]}'
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

    def get_image_dtos(self) -> List[ImageDto]:
        decoded_thumb = self._get_thumbnail_image()
        decoded_src = self.src_image
        thumb_height, thumb_width, _ = decoded_thumb.shape
        height, width, _ = decoded_src.shape

        return [
            ImageDto(
                key=self.base_key + self.THUMBNAIL_IMAGE_KEY_SUFFIX,
                byte=cv2.imencode('.jpg', decoded_thumb)[1].tobytes(),
                height=thumb_height,
                width=thumb_width,
                is_thumbnail=True,
            ),
            ImageDto(
                key=self.base_key + self.SOURCE_IMAGE_KEY_SUFFIX,
                byte=cv2.imencode('.jpg', decoded_src)[1].tobytes(),
                height=height,
                width=width,
                is_thumbnail=False,
            ),
        ]



