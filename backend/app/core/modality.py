"""CLIP-based chest X-ray modality check."""

from __future__ import annotations

import logging
from typing import Dict

import torch
from PIL import Image

logger = logging.getLogger(__name__)

CXR_PROMPTS = [
    "a chest x-ray radiograph",
    "a frontal chest x-ray",
    "a medical x-ray image of the chest",
    "a radiograph of the lungs and heart",
    "a PA chest radiograph",
    "an AP chest radiograph",
]

NON_CXR_PROMPTS = [
    "an MRI scan of the brain",
    "an MRI scan of the abdomen",
    "an MRI scan of the spine",
    "a CT scan of the chest",
    "a CT scan of the abdomen",
    "a CT scan of the head",
    "an ultrasound image",
    "a mammogram",
    "a pathology slide",
    "a photograph of a person",
    "a photograph of an object",
    "a photograph of food",
    "a screenshot of software",
    "a document or text",
    "a chart or graph",
    "a drawing or illustration",
    "a knee x-ray",
    "a dental x-ray",
    "a hand x-ray",
]

MODALITY_THRESHOLD = 0.5

_clip_state = {
    "loaded": False,
    "model": None,
    "preprocess": None,
    "text_features": None,
    "device": None,
}


def _load_clip():
    if _clip_state["loaded"]:
        return

    try:
        import open_clip
    except ImportError as e:
        logger.warning(f"modality_check_unavailable error={e}")
        _clip_state["loaded"] = True
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"loading_clip device={device}")

    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="laion2b_s34b_b79k"
    )
    model.eval()
    model.to(device)

    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    with torch.no_grad():
        tokens = tokenizer(CXR_PROMPTS + NON_CXR_PROMPTS).to(device)
        tf = model.encode_text(tokens)
        tf = tf / tf.norm(dim=-1, keepdim=True)

    _clip_state["model"] = model
    _clip_state["preprocess"] = preprocess
    _clip_state["text_features"] = tf
    _clip_state["device"] = device
    _clip_state["loaded"] = True
    logger.info(f"clip_loaded prompts={len(CXR_PROMPTS) + len(NON_CXR_PROMPTS)}")


def check_modality(image: Image.Image) -> Dict:
    """Determine whether an image is a chest X-ray using CLIP."""
    _load_clip()

    if _clip_state["model"] is None:
        return {
            "is_cxr": True,
            "cxr_score": 1.0,
            "best_non_cxr": "",
            "best_non_cxr_score": 0.0,
            "reason": "",
        }

    try:
        rgb = image.convert("RGB")
        tensor = _clip_state["preprocess"](rgb).unsqueeze(0).to(_clip_state["device"])

        with torch.no_grad():
            f = _clip_state["model"].encode_image(tensor)
            f = f / f.norm(dim=-1, keepdim=True)
            logits = 100.0 * f @ _clip_state["text_features"].T
            probs = logits.softmax(dim=-1)[0].tolist()

        n_cxr = len(CXR_PROMPTS)
        cxr_score = float(sum(probs[:n_cxr]))
        non_cxr_probs = probs[n_cxr:]

        if non_cxr_probs:
            best_idx = max(range(len(non_cxr_probs)), key=lambda i: non_cxr_probs[i])
            best_non_cxr = NON_CXR_PROMPTS[best_idx]
            best_score = float(non_cxr_probs[best_idx])
        else:
            best_non_cxr = ""
            best_score = 0.0

        is_cxr = cxr_score >= MODALITY_THRESHOLD

        reason = ""
        if not is_cxr:
            reason = (
                f"Image does not appear to be a chest X-ray "
                f"(CXR confidence {cxr_score * 100:.1f}%, "
                f"best match: {best_non_cxr})"
            )

        return {
            "is_cxr": is_cxr,
            "cxr_score": round(cxr_score, 4),
            "best_non_cxr": best_non_cxr,
            "best_non_cxr_score": round(best_score, 4),
            "reason": reason,
        }

    except Exception as e:
        logger.exception(f"modality_check_failed error={e}")
        return {
            "is_cxr": True,
            "cxr_score": 1.0,
            "best_non_cxr": "",
            "best_non_cxr_score": 0.0,
            "reason": "",
        }