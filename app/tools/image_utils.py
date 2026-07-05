import os
import base64
from typing import Dict, Any

def load_and_validate_image(image_path: str) -> Dict[str, Any]:
    """
    Checks that the file exists, has a supported format, and is under the size limit.

    Args:
        image_path: Path to the image file.

    Returns:
        Dict[str, Any]: Structured dictionary indicating validity and properties.
    """
    try:
        # Check file existence
        if not os.path.exists(image_path):
            return {"valid": False, "error": "File not found."}

        # Check extension (case-insensitive)
        _, ext = os.path.splitext(image_path)
        ext = ext.lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            return {"valid": False, "error": "Unsupported format. Use JPEG, PNG, or WEBP."}

        # Check size limit
        max_size_mb = float(os.getenv("TRUTHGUARD_MAX_IMAGE_SIZE_MB", "10"))
        file_size_bytes = os.path.getsize(image_path)
        if file_size_bytes > max_size_mb * 1024 * 1024:
            return {"valid": False, "error": "File exceeds size limit."}

        format_map = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".webp": "WEBP"
        }
        img_format = format_map.get(ext, "UNKNOWN")

        return {
            "valid": True,
            "image_path": image_path,
            "format": img_format,
            "size_bytes": file_size_bytes,
            "error": None
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}

def encode_image_for_gemini(image_path: str) -> Dict[str, Any]:
    """
    Encodes the image file as a base64 string and determines its MIME type.

    Args:
        image_path: Path to the image file.

    Returns:
        Dict[str, Any]: Base64-encoded string and matching MIME type.
    """
    try:
        if not os.path.exists(image_path):
            return {
                "base64_data": "",
                "mime_type": "",
                "error": "File not found."
            }

        with open(image_path, "rb") as image_file:
            encoded_bytes = base64.b64encode(image_file.read())
            base64_data = encoded_bytes.decode("utf-8")

        _, ext = os.path.splitext(image_path)
        ext = ext.lower()
        
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp"
        }
        mime_type = mime_map.get(ext, "application/octet-stream")

        return {
            "base64_data": base64_data,
            "mime_type": mime_type
        }
    except Exception as e:
        return {
            "base64_data": "",
            "mime_type": "",
            "error": str(e)
        }

def validate_image(file_path: str) -> Dict[str, Any]:
    """
    Compatibility wrapper matching the original validate_image signature.
    """
    res = load_and_validate_image(file_path)
    if res.get("valid") is True:
        return {
            "status": "success",
            "format": res.get("format"),
            "size_mb": res.get("size_bytes", 0) / (1024 * 1024)
        }
    return {
        "status": "error",
        "error_code": "IMAGE_VALIDATION_FAILED",
        "message": res.get("error", "Unknown validation error")
    }

