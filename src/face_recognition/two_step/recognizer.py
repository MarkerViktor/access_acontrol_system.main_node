from typing import Optional

from ..backend_protocols import Recognizer, Descriptor, NumpyImage
from ..face_recognition_protocols import NewDescriptors, RecognitionResult


class FaceRecognizer:
    def __init__(self, recognizer: Recognizer):
        self._recognizer = recognizer
        self._descriptors: dict[int, Descriptor] = dict()

        self.check_image_normalized = self._recognizer.check_image_normalized
        self.check_descriptor_valid = self._recognizer.check_descriptor_valid

    def update_descriptors(self, new_descriptors: NewDescriptors) -> None:
        self._descriptors.update(new_descriptors)

    def calculate_descriptor(self, normalizes_image: NumpyImage) -> Descriptor:
        return self._recognizer.extract_features(normalizes_image)

    def recognize(self, normalized_image: NumpyImage) -> RecognitionResult:
        descriptor = self._recognizer.extract_features(normalized_image)
        if descriptor_id := self._find_similar_descriptor(descriptor):
            return RecognitionResult(is_known_face=True, descriptor_id=descriptor_id)
        else:
            return RecognitionResult(is_known_face=False, descriptor=list(descriptor))

    def recognize_by_descriptor(self, descriptor: Descriptor) -> RecognitionResult:
        if descriptor_id := self._find_similar_descriptor(descriptor):
            return RecognitionResult(is_known_face=True, descriptor_id=descriptor_id)
        else:
            return RecognitionResult(is_known_face=False)

    def _find_similar_descriptor(self, descriptor: Descriptor) -> Optional[int]:
        are_similar = self._recognizer.compare_descriptors  # to avoid extra __getattr__
        for id_, checking_descriptor in self._descriptors.items():
            if are_similar(descriptor, checking_descriptor):
                return id_
        return None
