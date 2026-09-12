"""ONNX Runtime inference engine for chest X-ray pathology classification."""

import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import onnxruntime as ort

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class InferenceEngine:
    """Thread-safe ONNX inference engine (singleton)."""

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
        self.session = None
        self.labels: List[str] = [
            "Cardiomegaly",
            "Pleural Effusion",
            "Consolidation",
            "Atelectasis",
            "Pneumothorax",
        ]
        self.model_version = "unknown"
        self._load_model()

    def _load_model(self) -> None:
        """Load ONNX model into memory."""
        settings = get_settings()
        model_path = Path(settings.MODEL_PATH)

        if not model_path.exists():
            logger.warning(
                "model_not_found",
                path=str(model_path),
                fallback="running in mock mode",
            )
            return

        try:
            providers = ["CPUExecutionProvider"]
            if "CUDAExecutionProvider" in ort.get_available_providers():
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

            self.session = ort.InferenceSession(str(model_path), providers=providers)
            self.model_version = model_path.stem

            logger.info(
                "model_loaded",
                path=str(model_path),
                providers=self.session.get_providers(),
                labels=self.labels,
            )
        except Exception as e:
            logger.exception("model_load_failed", error=str(e))
            self.session = None

    @property
    def is_loaded(self) -> bool:
        return self.session is not None

    def predict(self, preprocessed: np.ndarray) -> Dict:
        """Run inference on a preprocessed tensor (1, 3, 224, 224)."""
        if self.session is None:
            return {
                "predictions": {label: 0.5 for label in self.labels},
                "confidence": 0.5,
                "model_version": "mock",
                "inference_time_ms": 0,
            }

        start = time.perf_counter()
        input_name = self.session.get_inputs()[0].name
        logits = self.session.run(None, {input_name: preprocessed})[0][0]
        probs = 1.0 / (1.0 + np.exp(-logits))
        elapsed_ms = (time.perf_counter() - start) * 1000

        predictions = {label: float(p) for label, p in zip(self.labels, probs)}
        confidence = float(np.max(probs))

        return {
            "predictions": predictions,
            "confidence": confidence,
            "model_version": self.model_version,
            "inference_time_ms": round(elapsed_ms, 2),
        }


def get_inference_engine() -> InferenceEngine:
    """Dependency injection helper for FastAPI."""
    return InferenceEngine()