"""Dual-model Grad-CAM with automatic architecture detection.

v4 checkpoint: classifier is nn.Sequential(Dropout, Linear(256), ReLU, Dropout, Linear)
v1 checkpoint: classifier is a plain nn.Linear
The loader inspects state_dict keys and builds the correct classifier.
"""

import base64
import io
import threading
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageDraw, ImageFont
from torchvision import models

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

V4_LABELS = ["Tuberculosis", "Pneumonia", "No TB/Pneumonia"]
V1_LABELS = ["Cardiomegaly", "Pleural Effusion", "Consolidation", "Atelectasis", "Pneumothorax"]


def _jet_colormap(gray: np.ndarray) -> np.ndarray:
    r = np.clip(1.5 - np.abs(4.0 * gray - 3.0), 0.0, 1.0)
    g = np.clip(1.5 - np.abs(4.0 * gray - 2.0), 0.0, 1.0)
    b = np.clip(1.5 - np.abs(4.0 * gray - 1.0), 0.0, 1.0)
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
    _draw_rounded_rect(draw, bg_box, max(6, padding), fill=(15, 23, 42, 190))
    grad = np.linspace(0, 1, bar_w).reshape(1, -1)
    grad = np.repeat(grad, bar_h, axis=0)
    bar_rgb = (_jet_colormap(grad) * 255).astype(np.uint8)
    img.paste(Image.fromarray(bar_rgb).convert("RGB"), (x0, y0))
    draw.rectangle([x0, y0, x0 + bar_w, y0 + bar_h], outline=(255, 255, 255, 200), width=1)
    font_size = max(9, int(bar_h * 1.3))
    try:
        font = ImageFont.truetype("arial.ttf", size=font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=font_size)
        except Exception:
            font = ImageFont.load_default()
    text_y = y0 + bar_h + max(2, int(padding * 0.4))
    draw.text((x0, text_y), "LOW", fill=(240, 240, 240, 230), font=font)
    try:
        bbox = draw.textbbox((0, 0), "HIGH", font=font)
        text_w = bbox[2] - bbox[0]
    except Exception:
        text_w = 24
    draw.text((x0 + bar_w - text_w, text_y), "HIGH", fill=(240, 240, 240, 230), font=font)
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
    """Detect the classifier architecture from state_dict keys and build it."""
    # v4 style: Sequential with dropout — has classifier.1.weight, classifier.4.weight
    if any(k == "classifier.1.weight" for k in state_dict_keys):
        return nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(1024, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(256, num_labels),
        )
    # v1 style: plain Linear — has classifier.weight only
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

            # Detect architecture from state_dict keys
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
                    logger.warning("gradcam_cam_none", label=label, model=target.name)
                    return None

                cam_img = Image.fromarray((cam * 255).astype(np.uint8))
                cam_img = cam_img.resize(original_image.size, Image.BILINEAR)
                cam_arr = np.array(cam_img, dtype=np.float32) / 255.0

                colored = _jet_colormap(cam_arr)
                original_arr = np.array(original_image.convert("RGB"), dtype=np.float32) / 255.0
                alpha = 0.45
                overlay = (1 - alpha) * original_arr + alpha * colored
                overlay = np.clip(overlay * 255, 0, 255).astype(np.uint8)
                overlay = _draw_colorbar(overlay)

                buffer = io.BytesIO()
                Image.fromarray(overlay).save(buffer, format="PNG", optimize=True)
                b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                logger.info("gradcam_generated", label=label, model=target.name)
                return f"data:image/png;base64,{b64}"
            except Exception as e:
                logger.exception("gradcam_generate_failed", error=str(e))
                return None


def get_gradcam_engine() -> GradCAMEngine:
    return GradCAMEngine()