from typing import Optional
from dataclasses import dataclass

from ..backend_protocols import Detector, Recognizer, Normalizer, NumpyImage, Descriptor


class FaceRecognition:
    def __init__(self, detector: Detector, normalizer: Normalizer,
                 recognizer: Recognizer):
        self._detector = detector
        self._normalizer = normalizer
        self._recognizer = recognizer
        self._descriptors: dict[str, Descriptor] = dict()

    def update_descriptors(self, new_descriptors: dict[str, Descriptor]):
        self._descriptors.update(new_descriptors)

    def recognize(self, image: NumpyImage) -> Optional['RecognitionResult']:
        faces = self._detector.find_faces(image)
        if len(faces) == 0:
            return None
        biggest_face = max(faces, key=lambda rect: rect.area)
        normalized_image = self._normalizer.normalize_image(image, biggest_face)
        descriptor = self._recognizer.extract_features(normalized_image)
        are_similar = self._recognizer.compare_descriptors
        for id_, tested_descriptor in self._descriptors.items():
            if are_similar(descriptor, tested_descriptor):
                return RecognitionResult(is_unknown_face=False, descriptor_id=id_)
        return RecognitionResult(is_unknown_face=True, descriptor=descriptor, image=normalized_image)


@dataclass
class RecognitionResult:
    is_unknown_face: bool
    descriptor_id: Optional[str] = None
    descriptor: Optional[Descriptor] = None
    image: Optional[NumpyImage] = None
