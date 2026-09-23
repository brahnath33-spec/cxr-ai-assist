"""Per-label clinical flagging thresholds.

Each finding has a threshold that reflects its clinical urgency and the
model's validated performance. A finding is flagged when its AI score
meets or exceeds its threshold.

IMPORTANT: These are NOT the same as the model's sigmoid output thresholds.
They are clinically-motivated operating points based on:
  - Emergency severity (Pneumothorax: 0.50)
  - Public health priority (Tuberculosis: 0.60)
  - Model reliability (Consolidation: 0.80 due to low AUC)
"""

CLINICAL_THRESHOLDS = {
    # === Validated findings (v4 + v1_fixed) ===
    "Tuberculosis": 0.60,
    "Pneumonia": 0.55,
    "Pleural Effusion": 0.70,
    "Pneumothorax": 0.50,   # emergency - highest sensitivity

    # === Informational findings (low AUC, requires higher bar) ===
    "Consolidation": 0.80,
    "Atelectasis": 0.80,

    # === Never flagged by AI score ===
    "Cardiomegaly": 1.01,        # CTR handles this, not AI score
    "No TB/Pneumonia": 1.01,     # "no disease" verdict is never a flag
}


def get_threshold(label: str) -> float:
    """Return the clinical flagging threshold for a finding."""
    return CLINICAL_THRESHOLDS.get(label, 0.5)