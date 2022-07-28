import numpy
import cv2
from typing import Tuple

class ImageSizeConverter:
    def __init__(self, image_bytes: bytes, extension: str = ".png"):
        self.image_bytes = image_bytes
        self.extension = extension
        self.np_array = cv2.imdecode(
            numpy.fromstring(
                self.image_bytes,
                numpy.uint8,
            ),
            cv2.IMREAD_COLOR,
        )

    def _get_range(self, side: float, length: int) -> Tuple[int]:
        if side > length:
            start = int((side / 2) - (length / 2))
            return start, start + length
        return 0, int(side)

    def crop(self, length: int) -> str:
        ranges = [self._get_range(side, length) for side in self.np_array.shape[:2]]
        array = self.np_array[ranges[0][0] : ranges[0][1], ranges[1][0] : ranges[1][1]]
        return cv2.imencode(self.extension, array)[1].tostring()

    def resize(self, width: int):
        h, w, _ = self.np_array.shape
        ratio = float(h) / float(w)
        height = round(ratio * width)
        return cv2.resize(
            self.np_array,
            dsize=(width, height),
            interpolation=cv2.INTER_LINEAR,
        )