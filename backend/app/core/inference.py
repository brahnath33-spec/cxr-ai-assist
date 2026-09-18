"""Dual-model inference engine. Returns 8 labels across v4 + v1 models."""

import time
from pathlib import Path
from typing import Dict

import numpy as np
import onnxruntime as ort

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

V4_LABELS = ["Tuberculosis", "Pneumonia", "No TB/Pneumonia"]
V1_LABELS = ["Cardiomegaly", "Pleural Effusion", "Consolidation", "Atelectasis", "Pneumothorax"]
ALL_LABELS = ["Tuberculosis", "Pneumonia", "Cardiomegaly", "Pleural Effusion",
              "Consolidation", "Atelectasis", "Pneumothorax", "No TB/Pneumonia"]


class InferenceEngine:
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
        self.session_v4 = None
        self.session_v1 = None
        self.labels = ALL_LABELS
        self.model_version = "best_cxrai_v4+v1"
        self._load_models()

    def _load_models(self) -> None:
        settings = get_settings()
        v4_path = Path(settings.MODEL_PATH)
        v1_path = Path(settings.LEGACY_MODEL_PATH)

        providers = ["CPUExecutionProvider"]
        if "CUDAExecutionProvider" in ort.get_available_providers():
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

        if v4_path.exists():
            try:
                self.session_v4 = ort.InferenceSession(str(v4_path), providers=providers)
                logger.info("model_loaded_v4", path=str(v4_path), labels=V4_LABELS)
            except Exception as e:
                logger.exception("model_v4_load_failed", error=str(e))
        else:
            logger.warning("model_v4_not_found", path=str(v4_path))

        if v1_path.exists():
            try:
                self.session_v1 = ort.InferenceSession(str(v1_path), providers=providers)
                logger.info("model_loaded_v1", path=str(v1_path), labels=V1_LABELS)
            except Exception as e:
                logger.exception("model_v1_load_failed", error=str(e))
        else:
            logger.warning("model_v1_not_found", path=str(v1_path))

    @property
    def is_loaded(self) -> bool:
        return self.session_v4 is not None or self.session_v1 is not None

    def _run_session(self, session, preprocessed: np.ndarray) -> np.ndarray:
        input_name = session.get_inputs()[0].name
        logits = session.run(None, {input_name: preprocessed})[0][0]
        return 1.0 / (1.0 + np.exp(-logits))

    def predict(self, preprocessed: np.ndarray) -> Dict:
        if not self.is_loaded:
            return {
                "predictions": {label: 0.0 for label in self.labels},
                "confidence": 0.0,
                "model_version": "mock",
                "inference_time_ms": 0,
            }

        start = time.perf_counter()
        predictions = {label: 0.0 for label in ALL_LABELS}

        if self.session_v4 is not None:
            probs_v4 = self._run_session(self.session_v4, preprocessed)
            predictions["Tuberculosis"] = float(probs_v4[0])
            predictions["Pneumonia"] = float(probs_v4[1])
            predictions["No TB/Pneumonia"] = float(probs_v4[2])

        if self.session_v1 is not None:
            probs_v1 = self._run_session(self.session_v1, preprocessed)
            predictions["Cardiomegaly"] = float(probs_v1[0])
            predictions["Pleural Effusion"] = float(probs_v1[1])
            predictions["Consolidation"] = float(probs_v1[2])
            predictions["Atelectasis"] = float(probs_v1[3])
            predictions["Pneumothorax"] = float(probs_v1[4])

        elapsed_ms = (time.perf_counter() - start) * 1000
        confidence = float(max(predictions.values()))

        return {
            "predictions": predictions,
            "confidence": confidence,
            "model_version": self.model_version,
            "inference_time_ms": round(elapsed_ms, 2),
        }


def get_inference_engine() -> InferenceEngine:
    return InferenceEngine()