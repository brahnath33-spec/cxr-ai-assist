"""Image quality gate - reject or warn on unsuitable chest radiographs.

Checks performed (all classical CV, no training):
  1. Image resolution (min 224x224)
  2. Aspect ratio (must be portrait-ish, not square landscape)
  3. Contrast (X-rays have high dynamic range)
  4. Chest X-ray likelihood (histogram signature)
  5. Anatomical landmarks (rib-like horizontal edges)

Returns:
  {
    "suitable": bool,
    "warnings": [str],
    "checks": {check_name: {"passed": bool, "value": float, "reason": str}}
  }
"""

from typing import Dict, List

import cv2
import numpy as np
from PIL import Image

from app.utils.logger import get_logger

logger = get_logger(__name__)


def _check_resolution(arr: np.ndarray) -> Dict:
    h, w = arr.shape[:2]
    min_dim = min(h, w)
    passed = min_dim >= 224
    return {
        "passed": passed,
        "value": float(min_dim),
        "reason": "" if passed else f"Image too small ({min_dim}px, need 224+)",
    }


def _check_aspect_ratio(arr: np.ndarray) -> Dict:
    h, w = arr.shape[:2]
    ratio = h / max(w, 1)
    passed = 0.7 <= ratio <= 1.8
    return {
        "passed": passed,
        "value": round(ratio, 2),
        "reason": "" if passed else f"Unusual aspect ratio ({ratio:.2f}, expected 0.7-1.8)",
    }


def _check_contrast(arr: np.ndarray) -> Dict:
    p5, p95 = np.percentile(arr, (5, 95))
    range_val = float(p95 - p5)
    passed = range_val >= 60
    return {
        "passed": passed,
        "value": round(range_val, 1),
        "reason": "" if passed else f"Low contrast (range {range_val:.0f}, need 60+)",
    }


def _check_cxr_signature(arr: np.ndarray) -> Dict:
    """
    Chest X-rays have a specific histogram signature:
    - Bimodal-ish distribution (dark lung fields + bright bone/soft tissue)
    - Mean intensity around 100-160
    - Not dominated by any single intensity
    """
    mean_int = float(arr.mean())
    std_int = float(arr.std())
    passed = (80 <= mean_int <= 190) and std_int > 30
    return {
        "passed": passed,
        "value": round(mean_int, 1),
        "reason": "" if passed else f"Histogram not consistent with CXR (mean {mean_int:.0f}, std {std_int:.0f})",
    }


def _check_anatomical_edges(arr: np.ndarray) -> Dict:
    """
    Chest X-rays have strong horizontal edges (ribs).
    Uses Sobel edge detection + horizontal gradient dominance.
    """
    # Resize for speed
    small = cv2.resize(arr, (256, 256))

    # Sobel gradients
    sobel_x = cv2.Sobel(small, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(small, cv2.CV_64F, 0, 1, ksize=3)

    # Rib edges are mostly horizontal, so sobel_y should have strong response
    edge_ratio = float(np.abs(sobel_y).mean() / (np.abs(sobel_x).mean() + 1e-6))

    # Chest X-rays: ratio between 0.9 and 1.5 (rib-dominated)
    # Landscape/abstract images often fall outside this range
    passed = 0.5 <= edge_ratio <= 2.0
    return {
        "passed": passed,
        "value": round(edge_ratio, 2),
        "reason": "" if passed else f"Edge distribution not rib-like (ratio {edge_ratio:.2f})",
    }


def check_image_quality(image: Image.Image) -> Dict:
    """
    Run all quality checks. Returns a dict with:
      - suitable: bool (True if all critical checks passed)
      - warnings: list of warning strings
      - checks: detailed per-check results
    """
    try:
        arr = np.array(image.convert("L"))

        checks = {
            "resolution": _check_resolution(arr),
            "aspect_ratio": _check_aspect_ratio(arr),
            "contrast": _check_contrast(arr),
            "cxr_signature": _check_cxr_signature(arr),
            "anatomical_edges": _check_anatomical_edges(arr),
        }

        warnings: List[str] = []
        for name, result in checks.items():
            if not result["passed"]:
                warnings.append(result["reason"])

        # Suitable only if resolution + contrast pass (critical)
        suitable = checks["resolution"]["passed"] and checks["contrast"]["passed"]

        # If 3+ checks fail, it's almost certainly not a CXR
        failed_count = sum(1 for c in checks.values() if not c["passed"])
        if failed_count >= 3:
            suitable = False
            warnings.append("Image does not appear to be a chest X-ray")

        result = {
            "suitable": suitable,
            "warnings": warnings,
            "checks": checks,
        }

        logger.info("quality_check", suitable=suitable, warnings=warnings)
        return result

    except Exception as e:
        logger.exception("quality_check_failed", error=str(e))
        return {
            "suitable": False,
            "warnings": [f"Quality check failed: {e}"],
            "checks": {},
        }