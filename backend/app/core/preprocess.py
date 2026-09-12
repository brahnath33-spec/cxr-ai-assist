"""Image preprocessing for chest X-ray inference (numpy + PIL only)."""

from io import BytesIO
from typing import Tuple

import numpy as np
from PIL import Image

TARGET_SIZE = 224
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def load_image_from_bytes(data: bytes) -> Image.Image:
    """Load a JPEG/PNG image from raw bytes."""
    return Image.open(BytesIO(data)).convert("RGB")


def preprocess_image(image: Image.Image) -> np.ndarray:
    """
    Resize, normalize, and format an image for ONNX inference.
    Returns: np.ndarray of shape (1, 3, 224, 224), dtype float32
    """
    img = image.resize((TARGET_SIZE, TARGET_SIZE), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
    arr = np.transpose(arr, (2, 0, 1))
    arr = np.expand_dims(arr, axis=0)
    return arr.astype(np.float32)


def preprocess_bytes(data: bytes) -> Tuple[np.ndarray, Image.Image]:
    """Convenience: bytes -> (preprocessed tensor, original PIL image)."""
    img = load_image_from_bytes(data)
    return preprocess_image(img), img