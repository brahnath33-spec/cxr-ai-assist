"""Cardiothoracic Ratio (CTR) measurement - classical image processing."""

from typing import Dict, Optional
import cv2
import numpy as np
from PIL import Image, ImageDraw
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _segment_lungs(image: Image.Image) -> np.ndarray:
    arr = np.array(image.convert("L"))
    h, w = arr.shape
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    eq = clahe.apply(arr)
    inv = 255 - eq
    _, thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    thresh[int(h * 0.78):, :] = 0
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8), iterations=2)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8), iterations=3)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    if num_labels <= 1:
        return np.ones((h, w), dtype=np.float32) * 0.5
    idxs = np.argsort(stats[1:, cv2.CC_STAT_AREA])[::-1][:3] + 1
    lung_mask = np.zeros((h, w), dtype=np.uint8)
    for idx in idxs:
        if stats[idx, cv2.CC_STAT_AREA] < (h * w) * 0.02:
            continue
        lung_mask[labels == idx] = 255
    lung_mask = cv2.GaussianBlur(lung_mask, (0, 0), sigmaX=max(h, w) * 0.015)
    lung_float = lung_mask.astype(np.float32) / 255.0
    if lung_float.max() < 0.3:
        return np.ones((h, w), dtype=np.float32) * 0.5
    return lung_float


def measure_ctr(image: Image.Image) -> Optional[Dict]:
    try:
        arr = np.array(image.convert("L"))
        h, w = arr.shape
        lung_mask = _segment_lungs(image)
        lung_binary = (lung_mask > 0.35).astype(np.uint8)
        rows_with_lung = np.where(lung_binary.sum(axis=1) > 10)[0]
        if len(rows_with_lung) < 10:
            return None
        top_row = int(rows_with_lung[0])
        bottom_row = int(rows_with_lung[-1])
        lung_height = bottom_row - top_row
        if lung_height < h * 0.3:
            return None

        heart_top = int(top_row + lung_height * 0.55)
        heart_bottom = int(bottom_row - lung_height * 0.05)
        best_row = None
        best_heart_width = 0
        best_heart_left = best_heart_right = 0
        mid = w // 2

        for r in range(heart_top, heart_bottom):
            row = lung_binary[r]
            left_half = np.where(row[:mid] > 0)[0]
            right_half = np.where(row[mid:] > 0)[0]
            if len(left_half) == 0 or len(right_half) == 0:
                continue
            left_lung_right = int(left_half.max())
            right_lung_left = int(right_half.min()) + mid
            gap = right_lung_left - left_lung_right
            if gap > best_heart_width and gap < (w * 0.8):
                best_heart_width = gap
                best_heart_left = left_lung_right
                best_heart_right = right_lung_left
                best_row = r

        if best_row is None or best_heart_width < 20:
            return None

        thorax_rows = range(max(0, best_row - 30), min(h, best_row + 30))
        best_thorax_width = 0
        best_thorax_left = best_thorax_right = 0
        for r in thorax_rows:
            row = lung_binary[r]
            cols = np.where(row > 0)[0]
            if len(cols) < 2: continue
            left = int(cols.min()); right = int(cols.max())
            if (right - left) > best_thorax_width:
                best_thorax_width = right - left
                best_thorax_left = left
                best_thorax_right = right

        if best_thorax_width < 50:
            return None

        ctr = best_heart_width / best_thorax_width
        if ctr >= 0.55: interpretation = "enlarged"
        elif ctr >= 0.50: interpretation = "borderline"
        else: interpretation = "normal"

        result = {
            "ctr": round(float(ctr), 3),
            "heart_width_px": int(best_heart_width),
            "thorax_width_px": int(best_thorax_width),
            "diaphragm_row": int(best_row),
            "heart_left_col": int(best_heart_left),
            "heart_right_col": int(best_heart_right),
            "thorax_left_col": int(best_thorax_left),
            "thorax_right_col": int(best_thorax_right),
            "interpretation": interpretation,
        }
        logger.info("ctr_measured", **result)
        return result
    except Exception as e:
        logger.exception("ctr_failed", error=str(e))
        return None