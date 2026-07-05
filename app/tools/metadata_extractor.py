import exifread
from typing import Dict, Any, List

def extract_metadata(image_path: str) -> Dict[str, Any]:
    """
    Extracts EXIF metadata using exifread and runs forensic validation checks.

    Args:
        image_path: Path to the local image file.

    Returns:
        Dict[str, Any]: Structured metadata analysis result.
    """
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)

        # Extract specific tags
        make_tag = tags.get("Image Make")
        model_tag = tags.get("Image Model")
        software_tag = tags.get("Image Software") or tags.get("Software")
        datetime_tag = tags.get("EXIF DateTimeOriginal")

        has_camera_make = bool(make_tag and str(make_tag).strip())
        has_camera_model = bool(model_tag and str(model_tag).strip())
        
        software = str(software_tag).strip() if software_tag else None
        datetime_original = str(datetime_tag).strip() if datetime_tag else None
        
        # Check if GPS info is present
        has_gps = any(key.startswith("GPS") for key in tags.keys())

        editing_software_detected = False
        anomaly_flags: List[str] = []

        # Open with PIL to read non-EXIF info chunks (PNG / WebP metadata)
        try:
            from PIL import Image
            with Image.open(image_path) as pil_img:
                pil_info = pil_img.info or {}
                for key, val in pil_info.items():
                    val_str = str(val).lower()
                    ai_keywords = [
                        "stable diffusion", "midjourney", "dall-e", 
                        "firefly", "runway", "invokeai", "automatic1111", "generator"
                    ]
                    if any(keyword in val_str for keyword in ai_keywords):
                        editing_software_detected = True
                        anomaly_flags.append("ai_software_detected")
        except Exception:
            pass

        # Check AI generative keywords in Software tag
        if software:
            software_lower = software.lower()
            ai_keywords = [
                "stable diffusion", "midjourney", "dall-e", 
                "firefly", "runway", "invokeai", "automatic1111"
            ]
            if any(keyword in software_lower for keyword in ai_keywords):
                editing_software_detected = True
                anomaly_flags.append("ai_software_detected")

        # Camera make/model anomaly
        if not has_camera_make and not has_camera_model:
            anomaly_flags.append("missing_camera_info")

        # Compile raw metadata representation
        raw_metadata: Dict[str, str] = {}
        for k, v in tags.items():
            if k not in ('JPEGThumbnail', 'TIFFThumbnail'):
                raw_metadata[k] = str(v)

        return {
            "has_camera_make": has_camera_make,
            "has_camera_model": has_camera_model,
            "software": software,
            "datetime_original": datetime_original,
            "has_gps": has_gps,
            "editing_software_detected": editing_software_detected,
            "anomaly_flags": anomaly_flags,
            "raw_metadata": raw_metadata
        }
    except Exception:
        # Gracefully handle all exceptions and return metadata_unreadable
        return {
            "has_camera_make": False,
            "has_camera_model": False,
            "software": None,
            "datetime_original": None,
            "has_gps": False,
            "editing_software_detected": False,
            "anomaly_flags": ["metadata_unreadable"],
            "raw_metadata": {}
        }
