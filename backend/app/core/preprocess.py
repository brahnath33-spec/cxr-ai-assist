"""Image preprocessing for chest X-ray inference."""

from io import BytesIO
from typing import Tuple

import numpy as np
from PIL import Image

from app.utils.dicom import is_dicom_file, dicom_to_pil

TARGET_SIZE = 224
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def load_image_from_bytes(data: bytes) -> Image.Image:
    """Load image from bytes. Auto-detects DICOM vs standard images."""
    if is_dicom_file(data):
        return dicom_to_pil(data, window_preset="default")
    return Image.open(BytesIO(data)).convert("RGB")


def preprocess_image(image: Image.Image) -> np.ndarray:
    img = image.resize((TARGET_SIZE, TARGET_SIZE), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
    arr = np.transpose(arr, (2, 0, 1))
    arr = np.expand_dims(arr, axis=0)
    return arr.astype(np.float32)


def preprocess_bytes(data: bytes) -> Tuple[np.ndarray, Image.Image]:
    img = load_image_from_bytes(data)
    return preprocess_image(img), img