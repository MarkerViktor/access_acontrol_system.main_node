import numpy as np
import cv2

from ..backend_protocols import NumpyImage, Rectangle
from ..utils import MODELS_PATH


OPENCV_MODELS = MODELS_PATH / 'opencv'
FACE_CASCADE_CLASSIFIER_PATH = OPENCV_MODELS / 'haarcascade_frontalface_default.xml'


class OpenCVDetector:
    def __init__(self):
        self._face_cascade_classifier = cv2.CascadeClassifier(str(FACE_CASCADE_CLASSIFIER_PATH))
        self.check_image_valid = _check_image_valid

    def find_faces(self, image: NumpyImage) -> tuple[Rectangle, ...]:
        faces = self._face_cascade_classifier.detectMultiScale(image, minNeighbors=15)
        return tuple(map(lambda f: Rectangle(*f), faces))


def _check_image_valid(image: NumpyImage) -> bool:
    shape, dtype = image.shape, image.dtype
    # check array type
    if dtype != np.uint8:
        return False
    # check array dimensions
    if len(shape) != 3:
        return False
    # check image channels
    if shape[2] not in {1, 3}:
        return False
    return True