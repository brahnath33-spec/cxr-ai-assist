"""Input validation — reject non-chest-X-ray images before inference.

Runs BEFORE the model. Prevents the model from returning confident
predictions on out-of-distribution inputs (brain MRI, CT, photos, etc.).
"""

from typing import Tuple

import numpy as np
from PIL import Image

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Tuning thresholds
MAX_ASPECT_RATIO = 2.5
MIN_ASPECT_RATIO = 0.4
MAX_COLORFULNESS = 20.0     # grayscale images are < 10; anything tinted exceeds this
MIN_MEAN_BRIGHTNESS = 30    # all-black images
MAX_MEAN_BRIGHTNESS = 220   # all-white images
MIN_INTENSITY_STD = 20      # flat images (no contrast)


def _colorfulness_score(rgb_arr: np.ndarray) -> float:
    """
    Hasler-Susstrunk colorfulness metric.
    0 for pure grayscale; rises quickly for tinted images.
    """
    r = rgb_arr[:, :, 0].astype(np.float32)
    g = rgb_arr[:, :, 1].astype(np.float32)
    b = rgb_arr[:, :, 2].astype(np.float32)

    rg = np.abs(r - g)
    yb = np.abs(0.5 * (r + g) - b)

    rg_mean, rg_std = rg.mean(), rg.std()
    yb_mean, yb_std = yb.mean(), yb.std()

    colorfulness = np.sqrt(rg_std ** 2 + rg_mean ** 2) + np.sqrt(yb_std ** 2 + yb_mean ** 2)
    return float(colorfulness)


def validate_chest_xray(image: Image.Image, filename: str = "unknown") -> Tuple[bool, str]:
    """
    Returns (is_valid, reason).
    If is_valid is False, reason contains a user-facing explanation.
    """
    try:
        # Aspect ratio check
        w, h = image.size
        ratio = w / h
        if ratio < MIN_ASPECT_RATIO or ratio > MAX_ASPECT_RATIO:
            reason = (
                f"Image dimensions {w}x{h} (aspect ratio {ratio:.2f}) do not match "
                f"a chest X-ray. Expected roughly square or portrait orientation."
            )
            logger.warning("validation_rejected", filename=filename, reason="aspect_ratio", ratio=ratio)
            return False, reason

        # Colorfulness check — X-rays are grayscale
        rgb_arr = np.array(image.convert("RGB"))
        cf = _colorfulness_score(rgb_arr)
        if cf > MAX_COLORFULNESS:
            reason = (
                f"Image contains significant color (colorfulness score {cf:.1f}). "
                f"Chest X-rays are grayscale — this may be a photograph, CT, MRI, or screenshot."
            )
            logger.warning("validation_rejected", filename=filename, reason="colorfulness", score=cf)
            return False, reason

        # Brightness + contrast check
        gray = np.array(image.convert("L")).astype(np.float32)
        mean_brightness = float(gray.mean())
        std_brightness = float(gray.std())

        if mean_brightness < MIN_MEAN_BRIGHTNESS:
            reason = "Image appears too dark — likely not a chest X-ray."
            logger.warning("validation_rejected", filename=filename, reason="too_dark", mean=mean_brightness)
            return False, reason
        if mean_brightness > MAX_MEAN_BRIGHTNESS:
            reason = "Image appears too bright — likely not a chest X-ray."
            logger.warning("validation_rejected", filename=filename, reason="too_bright", mean=mean_brightness)
            return False, reason
        if std_brightness < MIN_INTENSITY_STD:
            reason = "Image lacks sufficient contrast — likely not a chest X-ray."
            logger.warning("validation_rejected", filename=filename, reason="low_contrast", std=std_brightness)
            return False, reason

        logger.info("validation_passed", filename=filename, colorfulness=round(cf, 1), mean=round(mean_brightness, 1))
        return True, "ok"

    except Exception as e:
        logger.exception("validation_error", filename=filename, error=str(e))
        # Fail-open: if validation itself crashes, don't block the prediction
        return True, "validation_error"


def validate_chest_xray_bytes(data: bytes, filename: str = "unknown") -> Tuple[bool, str]:
    """Convenience: validate raw image bytes."""
    from io import BytesIO
    img = Image.open(BytesIO(data)).convert("RGB")
    return validate_chest_xray(img, filename)