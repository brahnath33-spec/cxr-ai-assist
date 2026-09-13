"""DICOM file handler for chest X-ray ingestion."""

from io import BytesIO

import numpy as np
import pydicom
from PIL import Image

from app.utils.logger import get_logger

logger = get_logger(__name__)

WINDOW_PRESETS = {
    "lung": {"center": -600, "width": 1500},
    "mediastinum": {"center": 40, "width": 400},
    "bone": {"center": 400, "width": 1800},
    "soft_tissue": {"center": 50, "width": 400},
    "default": {"center": None, "width": None},
}

PHI_TAGS_TO_STRIP = [
    "PatientName", "PatientID", "PatientBirthDate", "PatientSex",
    "PatientAge", "PatientAddress", "PatientTelephoneNumbers",
    "PatientMotherBirthName", "ReferringPhysicianName",
    "PerformingPhysicianName", "OperatorsName",
    "InstitutionName", "InstitutionAddress", "StudyID",
    "AccessionNumber", "OtherPatientIDs",
]


class DICOMHandler:
    @staticmethod
    def is_dicom(data):
        if len(data) < 132:
            return False
        return data[128:132] == b"DICM"

    @staticmethod
    def read_dicom(data):
        return pydicom.dcmread(BytesIO(data), force=True)

    @staticmethod
    def anonymize(ds):
        stripped = []
        for tag in PHI_TAGS_TO_STRIP:
            if hasattr(ds, tag):
                try:
                    delattr(ds, tag)
                    stripped.append(tag)
                except Exception:
                    try:
                        setattr(ds, tag, "ANONYMIZED")
                        stripped.append(tag)
                    except Exception:
                        pass
        if stripped:
            logger.info("dicom_anonymized", count=len(stripped))
        return ds

    @staticmethod
    def apply_window(pixel_array, wc, ww):
        if wc is None or ww is None:
            p2, p98 = np.percentile(pixel_array, (2, 98))
            if p98 - p2 < 1:
                p2, p98 = pixel_array.min(), pixel_array.max()
            windowed = np.clip((pixel_array - p2) / (p98 - p2 + 1e-6) * 255, 0, 255)
        else:
            lower = wc - ww / 2
            upper = wc + ww / 2
            windowed = np.clip((pixel_array - lower) / (upper - lower + 1e-6) * 255, 0, 255)
        return windowed.astype(np.uint8)

    @classmethod
    def to_pil_image(cls, data, window_preset="default"):
        ds = cls.read_dicom(data)
        ds = cls.anonymize(ds)
        pixel_array = ds.pixel_array.astype(np.float32)
        slope = getattr(ds, "RescaleSlope", 1)
        intercept = getattr(ds, "RescaleIntercept", 0)
        pixel_array = pixel_array * slope + intercept
        preset = WINDOW_PRESETS.get(window_preset, WINDOW_PRESETS["default"])
        windowed = cls.apply_window(pixel_array, preset["center"], preset["width"])
        photometric = getattr(ds, "PhotometricInterpretation", "MONOCHROME2")
        if photometric == "MONOCHROME1":
            windowed = 255 - windowed
        pil_image = Image.fromarray(windowed, mode="L").convert("RGB")
        logger.info("dicom_converted", shape=str(pixel_array.shape), preset=window_preset)
        return pil_image


def is_dicom_file(data):
    return DICOMHandler.is_dicom(data)


def dicom_to_pil(data, window_preset="default"):
    return DICOMHandler.to_pil_image(data, window_preset)