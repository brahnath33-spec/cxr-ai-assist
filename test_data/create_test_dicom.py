"""Generate a synthetic chest X-ray DICOM file for testing."""

import os
import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid
from PIL import Image, ImageDraw

# Absolute output path (works from anywhere)
OUTPUT_PATH = r"C:\Users\brahn\cxr-ai-assist\test_data\synthetic_chest_xray.dcm"

# Create a synthetic chest X-ray (grayscale 512x512)
size = 512
img = Image.new("L", (size, size), color=30)
draw = ImageDraw.Draw(img)

# Lung fields (darker regions)
draw.ellipse([80, 150, 240, 380], fill=60)
draw.ellipse([272, 150, 432, 380], fill=60)

# Heart silhouette (brighter)
draw.ellipse([200, 260, 320, 400], fill=140)

# Ribs (subtle horizontal lines)
for y in range(180, 380, 25):
    draw.line([80, y, 432, y], fill=100, width=2)

# Spine
draw.line([250, 100, 250, 450], fill=180, width=8)

# Noise
arr = np.array(img, dtype=np.float32)
arr += np.random.normal(0, 8, arr.shape)
arr = np.clip(arr, 0, 255).astype(np.uint16)

ds = Dataset()

file_meta = FileMetaDataset()
file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.1"
file_meta.MediaStorageSOPInstanceUID = generate_uid()
file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
file_meta.ImplementationClassUID = generate_uid()
ds.file_meta = file_meta

ds.PatientName = "TEST^PATIENT"
ds.PatientID = "TEST12345"
ds.PatientBirthDate = "19800101"
ds.PatientSex = "O"

ds.StudyInstanceUID = generate_uid()
ds.SeriesInstanceUID = generate_uid()
ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
ds.StudyID = "STUDY001"
ds.SeriesNumber = 1
ds.InstanceNumber = 1

ds.Modality = "CR"
ds.BodyPartExamined = "CHEST"
ds.ViewPosition = "PA"

ds.SamplesPerPixel = 1
ds.PhotometricInterpretation = "MONOCHROME2"
ds.Rows = size
ds.Columns = size
ds.BitsAllocated = 16
ds.BitsStored = 12
ds.HighBit = 11
ds.PixelRepresentation = 0
ds.RescaleSlope = 1
ds.RescaleIntercept = 0

ds.PixelData = arr.tobytes()

# Ensure output directory exists
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

ds.save_as(OUTPUT_PATH, enforce_file_format=True)

size_kb = os.path.getsize(OUTPUT_PATH) / 1024
print(f"SUCCESS: {OUTPUT_PATH}")
print(f"   Size: {size_kb:.1f} KB")
print(f"   Dimensions: {size}x{size}")