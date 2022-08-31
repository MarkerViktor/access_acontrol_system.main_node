from base64 import b85encode, b85decode
from zlib import compress, decompress
from pathlib import Path

from numpy import ndarray, float64

from .backend_protocols import Descriptor


def descriptor_to_str(descriptor: Descriptor, encoding: str = 'utf-8') -> str:
    return b85encode(compress(descriptor.tobytes())).decode(encoding)


def descriptor_from_str(string: str, encoding: str = 'utf-8') -> Descriptor:
    return ndarray(shape=(128,), dtype=float64,
                   buffer=decompress(b85decode(string.encode(encoding))))


MODELS_PATH = Path(__file__).parent / 'models'
