"""Grad-CAM explainability engine - forward hook + autograd.grad version."""

import base64
import io
import threading
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
        self.labels = []
        self.features = None
        self.lock = threading.Lock()
        self._load_model()

    def _load_model(self):
        settings = get_settings()
        ckpt_path = Path(settings.CHECKPOINT_PATH)
        if not ckpt_path.exists():
            logger.warning("gradcam_checkpoint_missing", path=str(ckpt_path))
            return
        try:
            checkpoint = torch.load(str(ckpt_path), map_location="cpu", weights_only=False)
            self.labels = checkpoint["labels"]
            model = models.densenet121(weights=None)
            model.classifier = nn.Linear(model.classifier.in_features, len(self.labels))
            model.load_state_dict(checkpoint["model_state_dict"])
            model.eval()
            model.features.norm5.register_forward_hook(self._save_features)
            self.model = model
            logger.info("gradcam_model_loaded", labels=self.labels)
        except Exception as e:
            logger.exception("gradcam_load_failed", error=str(e))
            self.model = None

    def _save_features(self, module, input, output):
        self.features = output

    @property
    def is_loaded(self):
        return self.model is not None

    def generate(self, preprocessed, original_image, label):
        if self.model is None or label not in self.labels:
            return None
        with self.lock:
            try:
                label_idx = self.labels.index(label)
                tensor = torch.from_numpy(preprocessed).clone()
                logits = self.model(tensor)
                score = logits[0, label_idx]
                features = self.features
                if features is None:
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
                cam_img = Image.fromarray((cam * 255).astype(np.uint8))
                cam_img = cam_img.resize(original_image.size, Image.BILINEAR)
                cam_arr = np.array(cam_img, dtype=np.float32) / 255.0
                colored = self._jet_colormap(cam_arr)
                orig_arr = np.array(original_image.convert("RGB"), dtype=np.float32) / 255.0
                overlay = (1 - 0.45) * orig_arr + 0.45 * colored
                overlay = np.clip(overlay * 255, 0, 255).astype(np.uint8)
                buffer = io.BytesIO()
                Image.fromarray(overlay).save(buffer, format="PNG", optimize=True)
                b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
                return f"data:image/png;base64,{b64}"
            except Exception as e:
                logger.exception("gradcam_generate_failed", error=str(e))
                return None

    @staticmethod
    def _jet_colormap(gray):
        r = np.clip(1.5 - np.abs(4.0 * gray - 3.0), 0.0, 1.0)
        g = np.clip(1.5 - np.abs(4.0 * gray - 2.0), 0.0, 1.0)
        b = np.clip(1.5 - np.abs(4.0 * gray - 1.0), 0.0, 1.0)
        return np.stack([r, g, b], axis=-1)


def get_gradcam_engine():
    return GradCAMEngine()