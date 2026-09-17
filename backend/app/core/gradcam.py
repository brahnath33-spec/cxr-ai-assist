"""Clinical-grade Grad-CAM for v4 CXR classifier.

Turbo colormap + percentile thresholding + Gaussian smoothing + top-right colorbar.
Produces radiology-grade saliency overlays suitable for publication.
"""

import base64
import io
import threading
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from torchvision import models

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Turbo colormap control points (Google, 2019)
TURBO_R = [0.18995, 0.27662, 0.24135, 0.12840, 0.19894, 0.59963, 0.94151, 0.98808, 0.93057, 0.74966, 0.48014]
TURBO_G = [0.07176, 0.30233, 0.54943, 0.75756, 0.88247, 0.93965, 0.85289, 0.65294, 0.35891, 0.17298, 0.01606]
TURBO_B = [0.23217, 0.79598, 0.92600, 0.78690, 0.54936, 0.25312, 0.15660, 0.13874, 0.09336, 0.03726, 0.00965]


def _turbo_colormap(gray: np.ndarray) -> np.ndarray:
    n_stops = len(TURBO_R)
    positions = np.linspace(0.0, 1.0, n_stops)
    r = np.interp(gray, positions, TURBO_R)
    g = np.interp(gray, positions, TURBO_G)
    b = np.interp(gray, positions, TURBO_B)
    return np.stack([r, g, b], axis=-1).astype(np.float32)


def _draw_colorbar(overlay_np: np.ndarray) -> np.ndarray:
    """
    Small, elegant Turbo-gradient colorbar in the TOP-RIGHT corner.
    Auto-scales with image size. Rounded corners. Publication-ready.
    """
    h, w = overlay_np.shape[:2]
    img = Image.fromarray(overlay_np)

    # Work on RGBA for semi-transparent background
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    # Small, elegant dimensions (scaled to image)
    bar_w = max(120, int(w * 0.10))           # narrower than before
    bar_h = max(8, int(h * 0.006))            # thinner bar
    margin = max(18, int(w * 0.018))          # tighter to edge
    padding = max(6, int(bar_h * 1.2))        # minimal padding

    # Position: TOP-RIGHT corner
    x0 = w - margin - bar_w - padding
    y0 = margin + padding

    # Rounded translucent background
    bg_box = [x0 - padding, y0 - padding, x0 + bar_w + padding, y0 + bar_h + padding * 4]
    radius = max(6, padding)
    _draw_rounded_rect(draw, bg_box, radius, fill=(15, 23, 42, 190))

    # Gradient bar (horizontal)
    grad = np.linspace(0, 1, bar_w).reshape(1, -1)
    grad = np.repeat(grad, bar_h, axis=0)
    bar_rgb = (_turbo_colormap(grad) * 255).astype(np.uint8)
    bar_img = Image.fromarray(bar_rgb).convert("RGB")
    img.paste(bar_img, (x0, y0))

    # Thin white border around the bar
    draw.rectangle([x0, y0, x0 + bar_w, y0 + bar_h], outline=(255, 255, 255, 200), width=1)

    # Small font
    font_size = max(9, int(bar_h * 1.3))
    try:
        font = ImageFont.truetype("arial.ttf", size=font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=font_size)
        except Exception:
            font = ImageFont.load_default()

    # Text labels below the bar
    text_y = y0 + bar_h + max(2, int(padding * 0.4))
    draw.text((x0, text_y), "LOW", fill=(240, 240, 240, 230), font=font)
    try:
        bbox = draw.textbbox((0, 0), "HIGH", font=font)
        text_w = bbox[2] - bbox[0]
    except Exception:
        text_w = 24
    draw.text((x0 + bar_w - text_w, text_y), "HIGH", fill=(240, 240, 240, 230), font=font)

    # Convert back to RGB
    return np.array(img.convert("RGB"))


def _draw_rounded_rect(draw, box, radius, fill):
    """Helper: rounded rectangle for cleaner look."""
    x0, y0, x1, y1 = box
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)
    draw.pieslice([x0, y0, x0 + 2*radius, y0 + 2*radius], 180, 270, fill=fill)
    draw.pieslice([x1 - 2*radius, y0, x1, y0 + 2*radius], 270, 360, fill=fill)
    draw.pieslice([x0, y1 - 2*radius, x0 + 2*radius, y1], 90, 180, fill=fill)
    draw.pieslice([x1 - 2*radius, y1 - 2*radius, x1, y1], 0, 90, fill=fill)


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
        self.model = None
        self.labels = ["Tuberculosis", "Pneumonia", "Normal"]
        self.features = None
        self.lock = threading.Lock()
        self._load_model()

    def _load_model(self) -> None:
        settings = get_settings()
        ckpt_path = Path(settings.CHECKPOINT_PATH)
        if not ckpt_path.exists():
            logger.warning("gradcam_checkpoint_missing", path=str(ckpt_path))
            return
        try:
            checkpoint = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
            self.labels = list(checkpoint.get("labels", self.labels))

            model = models.densenet121(weights=None)
            model.classifier = nn.Sequential(
                nn.Dropout(0.3),
                nn.Linear(model.classifier.in_features, 256),
                nn.ReLU(inplace=True),
                nn.Dropout(0.2),
                nn.Linear(256, len(self.labels)),
            )
            model.load_state_dict(checkpoint["model_state_dict"])
            model.eval()

            model.features.norm5.register_forward_hook(self._save_features)
            self.model = model
            logger.info("gradcam_model_loaded", path=str(ckpt_path), labels=self.labels)
        except Exception as e:
            logger.exception("gradcam_load_failed", error=str(e))
            self.model = None

    def _save_features(self, module, input, output):
        self.features = output

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def generate(self, preprocessed: np.ndarray, original_image: Image.Image, label: str) -> Optional[str]:
        if self.model is None:
            logger.warning("gradcam_not_loaded")
            return None
        if label not in self.labels:
            logger.warning("gradcam_unknown_label", label=label)
            return None

        with self.lock:
            try:
                label_idx = self.labels.index(label)
                tensor = torch.from_numpy(preprocessed).clone()
                logits = self.model(tensor)
                score = logits[0, label_idx]
                features = self.features
                if features is None:
                    logger.error("gradcam_no_features")
                    return None

                grads = torch.autograd.grad(score, features, retain_graph=False, create_graph=False)[0]
                grads_np = grads.detach().cpu().numpy()
                feats_np = features.detach().cpu().numpy()

                weights = grads_np.mean(axis=(2, 3), keepdims=True)
                cam = (weights * feats_np).sum(axis=1)[0]
                cam = np.maximum(cam, 0)

                cam_min, cam_max = cam.min(), cam.max()
                if cam_max - cam_min > 1e-8:
                    cam = (cam - cam_min) / (cam_max - cam_min)
                else:
                    cam = np.zeros_like(cam)

                # CLINICAL POLISH
                threshold = np.percentile(cam, 60)
                cam = np.where(cam >= threshold, cam, 0.0)
                cam_max2 = cam.max()
                if cam_max2 > 1e-8:
                    cam = cam / cam_max2

                cam_img = Image.fromarray((cam * 255).astype(np.uint8))
                cam_img = cam_img.resize(original_image.size, Image.BICUBIC)
                cam_img = cam_img.filter(ImageFilter.GaussianBlur(radius=5))
                cam_arr = np.array(cam_img, dtype=np.float32) / 255.0

                colored = _turbo_colormap(cam_arr)

                orig_arr = np.array(original_image.convert("RGB"), dtype=np.float32) / 255.0
                alpha = 0.40 * (cam_arr > 0.05).astype(np.float32)
                overlay = orig_arr * (1 - alpha[..., None]) + colored * alpha[..., None]
                overlay = np.clip(overlay * 255, 0, 255).astype(np.uint8)

                # Add top-right colorbar
                overlay = _draw_colorbar(overlay)

                buffer = io.BytesIO()
                Image.fromarray(overlay).save(buffer, format="PNG", optimize=True)
                b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                return f"data:image/png;base64,{b64}"
            except Exception as e:
                logger.exception("gradcam_generate_failed", error=str(e))
                return None


def get_gradcam_engine() -> GradCAMEngine:
    return GradCAMEngine()