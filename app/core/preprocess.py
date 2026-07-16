import cv2
import numpy as np

TARGET_WIDTH = 900


def clean(image_bytes: bytes) -> np.ndarray:
    gray = grayscale(image_bytes)
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        10,
    )


def grayscale(image_bytes: bytes) -> np.ndarray:
    image = _decode_and_resize(image_bytes)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def _decode_and_resize(image_bytes: bytes) -> np.ndarray:
    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image bytes")
    return _resize(image, TARGET_WIDTH)


def _resize(image: np.ndarray, target_width: int) -> np.ndarray:
    height, width = image.shape[:2]
    if width <= target_width:
        return image
    scale = target_width / width
    new_size = (target_width, round(height * scale))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
