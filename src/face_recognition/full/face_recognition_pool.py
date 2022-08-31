import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, Type, Iterable

from ..backend_protocols import (Detector, Normalizer, Recognizer,
                                 Descriptor, NumpyImage, Rectangle)
from ..face_recognition_protocols import NewDescriptors, RecognitionResult


class FaceRecognitionPool:
    def __init__(self,
                 detector: Type[Detector],
                 normalizer: Type[Normalizer],
                 recognizer: Type[Recognizer],
                 workers_quantity: int):
        self._pool = ProcessPoolExecutor(
            max_workers=workers_quantity,
            initializer=init_face_recognition_process,
            initargs=(detector, normalizer, recognizer)
        )
        self._descriptors: dict[int, Descriptor] = {}

        self.check_image_valid = detector.check_image_valid
        self.check_image_normalized = recognizer.check_image_normalized

    def update_descriptors(self, new_descriptors: NewDescriptors) -> None:
        self._descriptors.update(new_descriptors)

    async def calculator_descriptor(self, normalized_image: NumpyImage) -> Descriptor:
        future = self._pool.submit(extract_features, normalized_image)
        return await asyncio.wrap_future(future)

    async def recognize(self, normalizer_image: NumpyImage) -> RecognitionResult:
        descriptor = await self.calculator_descriptor(normalizer_image)
        if descriptor_id := self._find_similar_descriptor(descriptor):
            return RecognitionResult(is_known_face=True, descriptor_id=descriptor_id)
        else:
            return RecognitionResult(is_known_face=False, descriptor=list(descriptor))

    async def normalize(self, image: NumpyImage) -> Optional[NumpyImage]:
        face_rectangles = self._detector.find_faces(image)
        if face_rectangle := _find_biggest_rectangle(face_rectangles):
            return self._normalizer.normalize_image(image, face_rectangle)
        else:
            return None

    def _find_similar_descriptor(self, descriptor: Descriptor) -> Optional[int]:
        are_similar = self._recognizer.compare_descriptors  # to avoid extra __getattr__
        for id_, checking_descriptor in self._descriptors.items():
            if are_similar(descriptor, checking_descriptor):
                return id_
        return None

def _find_biggest_rectangle(face_rectangles: Iterable[Rectangle]) -> Optional[Rectangle]:
    if face_rectangles:
        return max(face_rectangles, key=lambda rect: rect.area)
    else:
        return None


_faces_detector: Detector
_face_image_normalizer: Normalizer
_face_recognizer: Recognizer


def init_face_recognition_process(detector, normalizer, recognizer):
    global _faces_detector, _face_image_normalizer, _face_recognizer
    _faces_detector = detector()
    _face_image_normalizer = normalizer()
    _face_recognizer = recognizer()


def detect_faces(image: NumpyImage) -> tuple[Rectangle]:
    global _faces_detector
    return _faces_detector.find_faces(image)


def normalize_face_image(image: NumpyImage, face_rectangle: Rectangle) -> NumpyImage:
    global _face_image_normalizer
    return _face_image_normalizer.normalize_image(image, face_rectangle)


def extract_features(image: NumpyImage) -> Descriptor:
    global _face_recognizer
    return _face_recognizer.extract_features(image)
