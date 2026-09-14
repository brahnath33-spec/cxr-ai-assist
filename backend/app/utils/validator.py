"""Input validation for chest X-ray inference.

Clinical-grade validation pipeline that rejects non-radiographic inputs
before inference. Uses multi-signal analysis consistent with the DICOM
standard for computed radiography (CR) and digital radiography (DX/DR).
"""

from io import BytesIO

import numpy as np
from PIL import Image

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Clinical thresholds
MIN_DIMENSION = 200
MAX_DIMENSION = 5000
MIN_ASPECT_RATIO = 0.4
MAX_ASPECT_RATIO = 2.5
MIN_GRAYSCALE_RATIO = 0.80
MAX_MEAN_SATURATION = 0.10
MAX_CHANNEL_SPREAD = 12
MAX_MEAN_BRIGHTNESS = 170
MAX_CORNER_BRIGHTNESS = 200
MIN_DARK_PIXEL_RATIO = 0.10
MIN_BIT_DEPTH = 30


class ValidationError(Exception):
    """Clinical input validation failure."""
    pass


def is_grayscale(img, threshold=MIN_GRAYSCALE_RATIO):
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    grayscale_mask = (
        (np.abs(r - g) < 12) & (np.abs(r - b) < 12) & (np.abs(g - b) < 12)
    )
    ratio = float(grayscale_mask.mean())
    return ratio >= threshold, ratio


def validate_dimensions(img):
    w, h = img.size
    if w < MIN_DIMENSION or h < MIN_DIMENSION:
        raise ValidationError(
            f"Study resolution below diagnostic threshold ({w}×{h} px). "
            f"A minimum of {MIN_DIMENSION}×{MIN_DIMENSION} pixels is required for chest radiograph analysis."
        )
    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        raise ValidationError(
            f"Study resolution exceeds processing limits ({w}×{h} px). "
            f"Maximum supported resolution is {MAX_DIMENSION}×{MAX_DIMENSION} pixels."
        )
    aspect = w / h
    if aspect < MIN_ASPECT_RATIO or aspect > MAX_ASPECT_RATIO:
        raise ValidationError(
            f"Projection geometry not consistent with chest radiograph standards "
            f"(aspect ratio {aspect:.2f}:1). Expected range: 0.4:1 to 2.5:1."
        )


def validate_bit_depth(img):
    unique_values = len(np.unique(np.asarray(img.convert("L"))))
    if unique_values < MIN_BIT_DEPTH:
        raise ValidationError(
            f"Study lacks sufficient dynamic range for diagnostic interpretation "
            f"({unique_values} distinct intensity levels detected)."
        )


def validate_saturation(img):
    hsv = np.asarray(img.convert("HSV"), dtype=np.float32)
    mean_sat = float((hsv[..., 1] / 255.0).mean())
    if mean_sat > MAX_MEAN_SATURATION:
        raise ValidationError(
            "Study is not monochrome. Chest radiographs must be presented in diagnostic grayscale format. "
            "Detected color channels are inconsistent with CR/DX/DR acquisition."
        )
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
    channel_spread = float(
        max(rgb[..., i].mean() for i in range(3)) -
        min(rgb[..., i].mean() for i in range(3))
    )
    if channel_spread > MAX_CHANNEL_SPREAD:
        raise ValidationError(
            "Study exhibits chromatic variance inconsistent with radiographic acquisition. "
            "Please verify the image is a diagnostic chest radiograph."
        )


def validate_brightness(img):
    arr = np.asarray(img.convert("L"), dtype=np.float32)
    mean_brightness = float(arr.mean())
    if mean_brightness > MAX_MEAN_BRIGHTNESS:
        raise ValidationError(
            "Study luminance is outside radiographic range. "
            "Chest radiographs present a dark background with radiolucent lung fields."
        )
    h, w = arr.shape
    corner_size = min(h, w) // 10
    corners = np.concatenate([
        arr[:corner_size, :corner_size].ravel(),
        arr[:corner_size, -corner_size:].ravel(),
        arr[-corner_size:, :corner_size].ravel(),
        arr[-corner_size:, -corner_size:].ravel(),
    ])
    if float(corners.mean()) > MAX_CORNER_BRIGHTNESS:
        raise ValidationError(
            "Corner luminance is inconsistent with chest radiograph field. "
            "Diagnostic radiographs show dark corners (background / lung apices)."
        )


def validate_dark_regions(img):
    arr = np.asarray(img.convert("L"), dtype=np.float32)
    dark_ratio = float((arr < 80).mean())
    if dark_ratio < MIN_DARK_PIXEL_RATIO:
        raise ValidationError(
            f"Insufficient radiolucent regions detected ({dark_ratio*100:.1f}% dark pixels). "
            "Chest radiographs contain significant dark background and aerated lung fields."
        )


def validate_dicom_metadata(ds):
    modality = getattr(ds, "Modality", None)
    if modality in ("CT", "MR", "US", "PT", "NM"):
        raise ValidationError(
            f"Study modality '{modality}' is not supported. "
            "CXR-AI Assist analyzes diagnostic chest radiographs (CR, DX, DR) only."
        )


def validate_image(img):
    validate_dimensions(img)
    validate_bit_depth(img)

    is_gray, gray_ratio = is_grayscale(img)
    if not is_gray:
        raise ValidationError(
            f"Study is not a monochrome radiographic image "
            f"({gray_ratio*100:.0f}% of pixels are grayscale; minimum 80% required). "
            "Please verify the uploaded file is a chest radiograph."
        )

    validate_saturation(img)
    validate_brightness(img)
    validate_dark_regions(img)

    logger.info("image_validation_passed", grayscale_ratio=round(gray_ratio, 3))


def validate_bytes(data):
    from app.utils.dicom import is_dicom_file, DICOMHandler
    if is_dicom_file(data):
        ds = DICOMHandler.read_dicom(data)
        validate_dicom_metadata(ds)
        img = DICOMHandler.to_pil_image(data, window_preset="default")
        validate_image(img)
        return img
    img = Image.open(BytesIO(data)).convert("RGB")
    validate_image(img)
    return img