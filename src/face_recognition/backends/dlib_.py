from pathlib import Path

import numpy as np
import dlib

from ..backend_protocols import Rectangle, NumpyImage, Descriptor
from ..utils import MODELS_PATH


DLIB_MODELS = MODELS_PATH / 'dlib'

SHAPE_PREDICTOR_PATH = DLIB_MODELS / 'shape_predictor_5_face_landmarks.dat'
FACE_RECOGNITION_MODEL_PATH = DLIB_MODELS / 'dlib_face_recognition_resnet_model_v1.dat'

NORMALIZED_IMAGE_SHAPE = (150, 150)
DESCRIPTOR_SHAPE = (128,)


class DlibDetector:
    def __init__(self, upsample_num_times: int = 1):
        self._upsample_num_times = upsample_num_times
        self._detector = dlib.get_frontal_face_detector()

        self.check_image_valid = _check_image_valid

    def find_faces(self, image: NumpyImage) -> tuple[Rectangle, ...]:
        dlib_rectangles = self._detector(image, self._upsample_num_times)
        return tuple(map(_convert_from_dlib_rect, dlib_rectangles))


class DlibNormalizer:
    def __init__(self, output_image_size: int = 150, face_padding: float = 0.25):
        self._shape_predictor = dlib.shape_predictor(str(SHAPE_PREDICTOR_PATH))
        self._output_image_size = output_image_size
        self._face_padding = face_padding

        self.check_image_valid = _check_image_valid

    def normalize_image(self, image: NumpyImage, face_rectangle: Rectangle) -> NumpyImage:
        shape = self._shape_predictor(image, _convert_to_dlib_rect(face_rectangle))
        aligned_face = dlib.get_face_chip(image, shape, self._output_image_size, self._face_padding)
        return aligned_face


class DlibRecognizer:
    # Maximal distance between face descriptors to confirm similarity
    _DISTANCE_THRESHOLD = 0.55

    def __init__(self, num_jitters: int = 0):
        self._recognizer = dlib.face_recognition_model_v1(str(FACE_RECOGNITION_MODEL_PATH))
        self._num_jitters = num_jitters

        self.check_image_normalized = _check_image_normalized
        self.check_descriptor_valid = _check_descriptor_valid

    def extract_features(self, normalized_image: NumpyImage) -> Descriptor:
        return np.array(self._recognizer.compute_face_descriptor(normalized_image))

    def compare_descriptors(self, descriptor_1: Descriptor, descriptor_2: Descriptor) -> bool:
        return np.linalg.norm(descriptor_2 - descriptor_1) < self._DISTANCE_THRESHOLD


def _check_image_normalized(image: NumpyImage) -> bool:
    if not _check_image_valid(image):
        return False
    height, width, _ = image.shape
    return (height, width) == NORMALIZED_IMAGE_SHAPE


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

def _check_descriptor_valid(descriptor: Descriptor):
    # check array type
    if descriptor.dtype not in (np.float64, np.float32):
        return False
    # check array shape
    if descriptor.shape != DESCRIPTOR_SHAPE:
        return False
    return True


def _convert_from_dlib_rect(dlib_rectangle: dlib.rectangle) -> Rectangle:
    rectangle = Rectangle(dlib_rectangle.left(), dlib_rectangle.top(),
                          dlib_rectangle.right() - dlib_rectangle.left(),
                          dlib_rectangle.bottom() - dlib_rectangle.top())
    return rectangle

def _convert_to_dlib_rect(rectangle: Rectangle) -> dlib.rectangle:
    dlib_rectangle = dlib.rectangle(rectangle.x, rectangle.y,
                                    rectangle.x + rectangle.width,
                                    rectangle.y + rectangle.height)
    return dlib_rectangle
