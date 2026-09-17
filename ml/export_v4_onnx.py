"""Export v4 CXR classifier to ONNX for fast inference."""

from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models

# Paths
CKPT_PATH = Path(r"C:\Users\brahn\cxr-ai-assist\ml\models\best_cxrai_v4.pth")
ONNX_PATH = Path(r"C:\Users\brahn\cxr-ai-assist\ml\models\best_cxrai_v4.onnx")

print(f"Loading checkpoint: {CKPT_PATH}")
checkpoint = torch.load(str(CKPT_PATH), map_location="cpu", weights_only=False)

LABELS = checkpoint["labels"]
print(f"Labels: {LABELS}")
print(f"Validation AUC: {checkpoint['val_auc']:.4f}")

# Rebuild DenseNet-121 architecture
model = models.densenet121(weights=None)
model.classifier = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(model.classifier.in_features, 256),
    nn.ReLU(inplace=True),
    nn.Dropout(0.2),
    nn.Linear(256, len(LABELS)),
)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

# Dummy input
dummy = torch.randn(1, 3, 224, 224)

# Export to ONNX
print(f"\nExporting to ONNX (opset 13)...")
torch.onnx.export(
    model,
    dummy,
    str(ONNX_PATH),
    input_names=["input"],
    output_names=["logits"],
    dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
    opset_version=13,
    do_constant_folding=True,
)

size_mb = ONNX_PATH.stat().st_size / (1024 * 1024)
print(f"\n✅ ONNX exported: {size_mb:.1f} MB")
print(f"   Path: {ONNX_PATH}")

# Verify it loads
import onnxruntime as ort
session = ort.InferenceSession(str(ONNX_PATH))
print(f"✅ ONNX runtime verified")
print(f"   Inputs: {session.get_inputs()[0].name}")
print(f"   Outputs: {session.get_outputs()[0].name}")