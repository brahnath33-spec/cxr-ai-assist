"""Diagnose v1 model - why is AUC only 0.62?"""

import torch
import torch.nn as nn
from torchvision import models
from pathlib import Path

CKPT = Path("C:/Users/brahn/cxr-ai-assist/ml/models/best_densenet121_chexpert.pth")

print("=" * 60)
print("V1 MODEL DIAGNOSTIC")
print("=" * 60)

ckpt = torch.load(str(CKPT), map_location="cpu", weights_only=False)
print(f"Checkpoint keys: {list(ckpt.keys())}")
print(f"Labels: {ckpt.get('labels', 'N/A')}")
print(f"Reported AUC: {ckpt.get('val_auc', 'N/A')}")
print(f"Epoch: {ckpt.get('epoch', 'N/A')}")

sd = ckpt["model_state_dict"]
print(f"\nState dict keys (first 5): {list(sd.keys())[:5]}")
print(f"State dict keys (last 5): {list(sd.keys())[-5:]}")

classifier_keys = [k for k in sd.keys() if "classifier" in k]
print(f"\nClassifier keys: {classifier_keys}")

for k in ["classifier.weight", "classifier.1.weight", "classifier.4.weight"]:
    if k in sd:
        w = sd[k]
        print(f"\n{k}: shape={w.shape}, mean={w.mean():.4f}, std={w.std():.4f}")

first_conv = sd.get("features.conv0.weight")
if first_conv is not None:
    print(f"\nfeatures.conv0.weight: mean={first_conv.mean():.4f}, std={first_conv.std():.4f}")
    if first_conv.std() < 0.001:
        print("FEATURE EXTRACTOR WEIGHTS ARE NEARLY CONSTANT - model is untrained!")
    else:
        print("Feature extractor weights look trained")