from dataclasses import dataclass
from typing import Protocol, Union, Mapping, Iterable, Optional

from .backend_protocols import Descriptor, NumpyImage


NewDescriptors = Union[Mapping[int, Descriptor], Iterable[tuple[int, Descriptor]]]

@dataclass
class RecognitionResult:
    is_known_face: Optional[bool] = None
    descriptor_id: Optional[int] = None
    descriptor: Optional[list[float]] = None


class FaceRecognition(Protocol):
    def update_descriptors(self, new_descriptors: NewDescriptors) -> None: ...

    def calculate_descriptor(self, normalized_image: NumpyImage) -> Descriptor: ...

    def recognize(self, normalized_image: NumpyImage) -> RecognitionResult: ...

    def normalize(self, image: NumpyImage) -> Optional[NumpyImage]: ...

    def check_image_normalized(self) -> bool: ...

    def check_image_valid(self) -> bool: ...


class AsyncFaceRecognition(Protocol):
    def update_descriptors(self, new_descriptors: NewDescriptors) -> None: ...

    async def calculate_descriptor(self, normalized_image: NumpyImage) -> Descriptor: ...

    async def recognize(self, normalized_image: NumpyImage) -> RecognitionResult: ...

    async def normalize(self, image: NumpyImage) -> Optional[NumpyImage]: ...

    def check_image_normalized(self) -> bool: ...

    def check_image_valid(self) -> bool: ...
