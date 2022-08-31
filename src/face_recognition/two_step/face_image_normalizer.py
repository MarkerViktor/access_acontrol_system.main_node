from typing import Optional, Iterable

from ..backend_protocols import Detector, Normalizer, NumpyImage, Rectangle


class FaceImageNormalizer:
    def __init__(self, detector: Detector, normalizer: Normalizer):
        self._detector = detector
        self._normalizer = normalizer

        self.check_image_valid = self._detector.check_image_valid

    def normalize(self, image: NumpyImage) -> Optional[NumpyImage]:
        face_rectangles = self._detector.find_faces(image)
        if face_rectangle := _find_biggest_rectangle(face_rectangles):
            return self._normalizer.normalize_image(image, face_rectangle)
        else:
            return None

def _find_biggest_rectangle(face_rectangles: Iterable[Rectangle]) -> Optional[Rectangle]:
    if face_rectangles:
        return max(face_rectangles, key=lambda rect: rect.area)
    else:
        return None
