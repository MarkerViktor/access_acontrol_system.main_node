from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray


@dataclass
class Rectangle:
    x: int
    y: int
    width: int
    height: int

    @property
    def area(self) -> int:
        return self.width * self.height


Descriptor = NDArray[np.float64]
NumpyImage = NDArray[np.uint8]


class Detector(Protocol):
    def find_faces(self, image: NumpyImage) -> tuple[Rectangle, ...]: ...

    def check_image_valid(self, image: NumpyImage) -> bool: ...


class Normalizer(Protocol):
    def normalize_image(self, image: NumpyImage, face_rectangle: Rectangle) -> NumpyImage: ...

    def check_image_valid(self, image: NumpyImage) -> bool: ...


class Recognizer(Protocol):
    def extract_features(self, normalized_image: NumpyImage) -> Descriptor: ...

    def compare_descriptors(self, descriptor_1: Descriptor, descriptor_2: Descriptor) -> bool: ...

    def check_image_normalized(self, image: NumpyImage) -> bool: ...

    def check_descriptor_valid(self, descriptor: Descriptor) -> bool: ...
