"""Export v1_fixed.pth to ONNX for backend inference."""

import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path

CKPT = Path("C:/Users/brahn/cxr-ai-assist/ml/models/v1_fixed.pth")
ONNX = Path("C:/Users/brahn/cxr-ai-assist/ml/models/v1_fixed.onnx")

print(f"Loading: {CKPT}")
ckpt = torch.load(str(CKPT), map_location="cpu", weights_only=False)
labels = ckpt["labels"]
print(f"Labels: {labels}")
print(f"AUC: {ckpt.get('best_auc', 'N/A')}")

model = models.densenet121(weights=None)
model.classifier = nn.Sequential(
    nn.Dropout(0.3),
    nn.Linear(model.classifier.in_features, 256),
    nn.ReLU(inplace=True),
    nn.Dropout(0.2),
    nn.Linear(256, len(labels)),
)
model.load_state_dict(ckpt["model_state_dict"])
model.eval()

dummy = torch.randn(1, 3, 224, 224)
torch.onnx.export(
    model, dummy, str(ONNX),
    input_names=["input"], output_names=["logits"],
    dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
    opset_version=17,
    do_constant_folding=True,
    dynamo=False,
)

size_mb = ONNX.stat().st_size / (1024 * 1024)
print(f"\n✅ Exported: {size_mb:.1f} MB")
print(f"   Path: {ONNX}")

import onnxruntime as ort
sess = ort.InferenceSession(str(ONNX), providers=["CPUExecutionProvider"])
print(f"   Verified: {sess.get_inputs()[0].name} -> {sess.get_outputs()[0].name}")