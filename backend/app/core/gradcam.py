"""Lung-masked Grad-CAM — replicates the CAD4TB visual style.

1. Approximate lung segmentation from the X-ray intensity
2. Compute Grad-CAM as usual
3. Mask the CAM to the lung region only
4. Apply smooth colormap and heavy Gaussian blur
5. Produce clinical, publication-grade heatmaps
"""

import base64
import io
import threading
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from torchvision import models

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

V4_LABELS = ["Tuberculosis", "Pneumonia", "No TB/Pneumonia"]
V1_LABELS = ["Cardiomegaly", "Pleural Effusion", "Consolidation", "Atelectasis", "Pneumothorax"]


# ============================================================
# LUNG SEGMENTATION (classical, no model needed)
# ============================================================

def _segment_lungs(image: Image.Image) -> np.ndarray:
    """
    Approximate lung mask from X-ray intensity.
    Lungs = dark regions in upper 75% of image, bilaterally symmetric.
    Returns a soft mask (0.0 to 1.0) same size as image.
    """
    arr = np.array(image.convert("L"))
    h, w = arr.shape

    # 1. CLAHE for local contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    eq = clahe.apply(arr)

    # 2. Invert (lungs become bright on dark background)
    inv = 255 - eq

    # 3. Threshold with Otsu
    _, thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 4. Restrict to upper 75% (exclude abdomen)
    thresh[int(h * 0.78):, :] = 0

    # 5. Remove thin structures (bones, ribs) with erosion then dilate (open)
    kernel_small = np.ones((5, 5), np.uint8)
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_small, iterations=2)

    # 6. Close small gaps
    kernel_large = np.ones((15, 15), np.uint8)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_large, iterations=3)

    # 7. Keep only the largest components (left + right lung)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    if num_labels <= 1:
        return np.ones((h, w), dtype=np.float32)  # fallback: no mask

    # Sort by area, take top 3 (usually left lung, right lung, sometimes 1 noise)
    idxs = np.argsort(stats[1:, cv2.CC_STAT_AREA])[::-1][:3] + 1
    lung_mask = np.zeros((h, w), dtype=np.uint8)
    for idx in idxs:
        area = stats[idx, cv2.CC_STAT_AREA]
        if area < (h * w) * 0.02:  # skip tiny fragments
            continue
        lung_mask[labels == idx] = 255

    # 8. Feather the edges — soft mask (avoids hard boundary lines)
    lung_mask = cv2.GaussianBlur(lung_mask, (0, 0), sigmaX=max(h, w) * 0.015)

    # 9. Normalize to 0-1
    lung_float = lung_mask.astype(np.float32) / 255.0

    # 10. Ensure minimum signal (if segmentation failed, keep it soft)
    if lung_float.max() < 0.3:
        return np.ones((h, w), dtype=np.float32)

    return lung_float


# ============================================================
# CLINICAL COLORMAP (red → yellow → green → blue)
# ============================================================

def _clinical_colormap(gray: np.ndarray) -> np.ndarray:
    """
    Clinical heatmap palette matching CAD4TB style:
    blue (low) → green → yellow → red (high)
    Softer than jet, more medical-looking.
    """
    r = np.clip(2.2 * gray - 0.6, 0.0, 1.0)
    g = np.clip(2.0 * gray - 0.3, 0.0, 1.0)
    b = np.clip(1.8 * (1.0 - gray) * (gray > 0.05).astype(np.float32), 0.0, 1.0)
    # Add faint blue even at high values to keep the "medical" look
    b = np.clip(b + 0.15 * (1 - gray), 0.0, 1.0)
    return np.stack([r, g, b], axis=-1).astype(np.float32)


def _draw_colorbar(overlay_np: np.ndarray) -> np.ndarray:
    h, w = overlay_np.shape[:2]
    img = Image.fromarray(overlay_np).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")
    bar_w = max(120, int(w * 0.10))
    bar_h = max(8, int(h * 0.006))
    margin = max(18, int(w * 0.018))
    padding = max(6, int(bar_h * 1.2))
    x0 = w - margin - bar_w - padding
    y0 = margin + padding
    bg_box = [x0 - padding, y0 - padding, x0 + bar_w + padding, y0 + bar_h + padding * 4]
    _draw_rounded_rect(draw, bg_box, max(6, padding), fill=(15, 23, 42, 200))
    grad = np.linspace(0, 1, bar_w).reshape(1, -1)
    grad = np.repeat(grad, bar_h, axis=0)
    bar_rgb = (_clinical_colormap(grad) * 255).astype(np.uint8)
    img.paste(Image.fromarray(bar_rgb).convert("RGB"), (x0, y0))
    draw.rectangle([x0, y0, x0 + bar_w, y0 + bar_h], outline=(255, 255, 255, 220), width=1)
    font_size = max(9, int(bar_h * 1.3))
    try:
        font = ImageFont.truetype("arial.ttf", size=font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=font_size)
        except Exception:
            font = ImageFont.load_default()
    text_y = y0 + bar_h + max(2, int(padding * 0.4))
    draw.text((x0, text_y), "LOW", fill=(240, 240, 240, 235), font=font)
    try:
        bbox = draw.textbbox((0, 0), "HIGH", font=font)
        text_w = bbox[2] - bbox[0]
    except Exception:
        text_w = 24
    draw.text((x0 + bar_w - text_w, text_y), "HIGH", fill=(240, 240, 240, 235), font=font)
    return np.array(img.convert("RGB"))


def _draw_rounded_rect(draw, box, radius, fill):
    x0, y0, x1, y1 = box
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.pieslice([x0, y0, x0 + 2*radius, y0 + 2*radius], 180, 270, fill=fill)
    draw.pieslice([x1 - 2*radius, y0, x1, y0 + 2*radius], 270, 360, fill=fill)
    draw.pieslice([x0, y1 - 2*radius, x0 + 2*radius, y1], 90, 180, fill=fill)
    draw.pieslice([x1 - 2*radius, y1 - 2*radius, x1, y1], 0, 90, fill=fill)


def _build_classifier(state_dict_keys: List[str], num_labels: int) -> nn.Module:
    if any(k == "classifier.1.weight" for k in state_dict_keys):
        return nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(1024, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(256, num_labels),
        )
    return nn.Linear(1024, num_labels)


class _SingleModel:
    def __init__(self, checkpoint_path: Path, expected_labels: List[str], name: str):
        self.name = name
        self.model = None
        self.labels = list(expected_labels)
        self.features = None

        if not checkpoint_path.exists():
            logger.warning("gradcam_checkpoint_missing", name=name, path=str(checkpoint_path))
            return
        try:
            checkpoint = torch.load(str(checkpoint_path), map_location="cpu", weights_only=False)
            state_dict = checkpoint["model_state_dict"]
            raw_labels = list(checkpoint.get("labels", expected_labels))
            self.labels = ["No TB/Pneumonia" if l == "Normal" else l for l in raw_labels]

            keys = list(state_dict.keys())
            classifier = _build_classifier(keys, len(self.labels))

            model = models.densenet121(weights=None)
            model.classifier = classifier
            model.load_state_dict(state_dict)
            model.eval()
            model.features.norm5.register_forward_hook(self._save_features)
            self.model = model
            logger.info("gradcam_model_loaded", name=name, path=str(checkpoint_path),
                        labels=self.labels, classifier=classifier.__class__.__name__)
        except Exception as e:
            logger.exception("gradcam_load_failed", name=name, path=str(checkpoint_path), error=str(e))

    def _save_features(self, module, input, output):
        self.features = output

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def has_label(self, label: str) -> bool:
        return self.loaded and label in self.labels

    def compute_cam(self, preprocessed: np.ndarray, label: str) -> Optional[np.ndarray]:
        if not self.has_label(label):
            return None
        idx = self.labels.index(label)
        tensor = torch.from_numpy(preprocessed).clone()
        logits = self.model(tensor)
        score = logits[0, idx]
        features = self.features
        if features is None:
            return None
        grads = torch.autograd.grad(score, features, retain_graph=False, create_graph=False)[0]
        grads_np = grads.detach().cpu().numpy()
        feats_np = features.detach().cpu().numpy()
        weights = grads_np.mean(axis=(2, 3), keepdims=True)
        cam = (weights * feats_np).sum(axis=1)[0]
        cam = np.maximum(cam, 0)
        cmin, cmax = cam.min(), cam.max()
        if cmax - cmin > 1e-8:
            cam = (cam - cmin) / (cmax - cmin)
        else:
            cam = np.zeros_like(cam)
        return cam


class GradCAMEngine:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.lock = threading.Lock()

        settings = get_settings()
        self.v4 = _SingleModel(Path(settings.CHECKPOINT_PATH), V4_LABELS, "v4")
        legacy_path = getattr(settings, "LEGACY_CHECKPOINT_PATH", None)
        self.v1 = _SingleModel(Path(legacy_path), V1_LABELS, "v1") if legacy_path else None

    @property
    def is_loaded(self) -> bool:
        return (self.v4 and self.v4.loaded) or (self.v1 and self.v1.loaded)

    def _pick_model(self, label: str) -> Optional[_SingleModel]:
        if self.v4 and self.v4.has_label(label):
            return self.v4
        if self.v1 and self.v1.has_label(label):
            return self.v1
        return None

    def generate(self, preprocessed: np.ndarray, original_image: Image.Image, label: str) -> Optional[str]:
        target = self._pick_model(label)
        if target is None:
            logger.warning("gradcam_unknown_label", requested=label)
            return None

        with self.lock:
            try:
                cam = target.compute_cam(preprocessed, label)
                if cam is None:
                    return None

                # Upscale CAM to image size
                cam_img = Image.fromarray((cam * 255).astype(np.uint8))
                cam_img = cam_img.resize(original_image.size, Image.BICUBIC)

                # LUNG MASK — the CAD4TB trick
                lung_mask = _segment_lungs(original_image)
                cam_arr = np.array(cam_img, dtype=np.float32) / 255.0
                masked_cam = cam_arr * lung_mask  # zero outside lungs

                # Heavy blur for smooth anatomical boundaries
                cam_blur = Image.fromarray((masked_cam * 255).astype(np.uint8))
                cam_blur = cam_blur.filter(ImageFilter.GaussianBlur(radius=max(8, original_image.size[0] // 150)))
                cam_final = np.array(cam_blur, dtype=np.float32) / 255.0

                # Re-normalize after masking
                cmax = cam_final.max()
                if cmax > 0.05:
                    cam_final = cam_final / cmax

                # Clinical colormap
                colored = _clinical_colormap(cam_final)

                # Blend only where signal exists
                original_arr = np.array(original_image.convert("RGB"), dtype=np.float32) / 255.0
                alpha = 0.55 * (cam_final > 0.08).astype(np.float32)
                overlay = original_arr * (1 - alpha[..., None]) + colored * alpha[..., None]
                overlay = np.clip(overlay * 255, 0, 255).astype(np.uint8)

                overlay = _draw_colorbar(overlay)

                buffer = io.BytesIO()
                Image.fromarray(overlay).save(buffer, format="PNG", optimize=True)
                b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                logger.info("gradcam_generated", label=label, model=target.name, masked=True)
                return f"data:image/png;base64,{b64}"
            except Exception as e:
                logger.exception("gradcam_generate_failed", error=str(e))
                return None


def get_gradcam_engine() -> GradCAMEngine:
    return GradCAMEngine()