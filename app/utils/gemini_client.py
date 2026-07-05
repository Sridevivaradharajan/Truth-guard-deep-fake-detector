import os
import time
import base64
from typing import Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

# Load all configurations from .env
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

VISION_MODEL    = os.getenv("TRUTHGUARD_VISION_MODEL",    "gemini-2.5-flash")
TEXT_MODEL      = os.getenv("TRUTHGUARD_TEXT_MODEL",      "gemini-2.5-flash-lite")
API_CALL_DELAY  = float(os.getenv("TRUTHGUARD_API_CALL_DELAY",  "2.0"))
MAX_RETRIES     = int(os.getenv("TRUTHGUARD_MAX_RETRIES",       "3"))
RETRY_BASE_WAIT = int(os.getenv("TRUTHGUARD_RETRY_BASE_WAIT",   "10"))

def call_text_model(prompt: str) -> Dict[str, Any]:
    """
    Call TRUTHGUARD_TEXT_MODEL (Flash-Lite) for all text-only tasks.

    Args:
        prompt: The text prompt.

    Returns:
        Dict[str, Any]: The structured response dict.
    """
    # Step 1: Sleep for API_CALL_DELAY seconds before every call
    time.sleep(API_CALL_DELAY)

    for attempt in range(MAX_RETRIES):
        try:
            # Step 2: Call generate_content
            model = genai.GenerativeModel(TEXT_MODEL)
            response = model.generate_content(prompt)
            # Step 3: On success return
            return {
                "success": True,
                "text": response.text,
                "error": None
            }
        except Exception as e:
            err_msg = str(e).lower()
            is_quota_error = "429" in err_msg or "quota" in err_msg
            
            # Step 4: On any exception containing "429" or "quota"
            if is_quota_error:
                if attempt < MAX_RETRIES - 1:
                    sleep_duration = RETRY_BASE_WAIT * (2 ** attempt)
                    time.sleep(sleep_duration)
                    continue
                else:
                    return {
                        "success": False,
                        "text": "",
                        "error": f"Quota limit reached after {MAX_RETRIES} retries. Wait and try again."
                    }
            else:
                # Step 5: On any other exception
                return {
                    "success": False,
                    "text": "",
                    "error": str(e)
                }

    return {
        "success": False,
        "text": "",
        "error": f"Quota limit reached after {MAX_RETRIES} retries. Wait and try again."
    }

def call_vision_model(prompt: str, image_base64: str, mime_type: str) -> Dict[str, Any]:
    """
    Call TRUTHGUARD_VISION_MODEL (Flash) for image analysis tasks.

    Args:
        prompt: The text prompt.
        image_base64: Base64-encoded image string.
        mime_type: MIME type of the image.

    Returns:
        Dict[str, Any]: The structured response dict.
    """
    # Step 1: Sleep for API_CALL_DELAY seconds before every call
    time.sleep(API_CALL_DELAY)

    try:
        # Step 2: Build image_part
        image_part = {
            "mime_type": mime_type,
            "data": base64.b64decode(image_base64)
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Base64 decoding failed: {str(e)}"
        }

    for attempt in range(MAX_RETRIES):
        try:
            # Step 3: Call generate_content
            model = genai.GenerativeModel(VISION_MODEL)
            response = model.generate_content([prompt, image_part])
            return {
                "success": True,
                "text": response.text,
                "error": None
            }
        except Exception as e:
            err_msg = str(e).lower()
            is_quota_error = "429" in err_msg or "quota" in err_msg
            
            # Step 4: On any exception containing "429" or "quota"
            if is_quota_error:
                if attempt < MAX_RETRIES - 1:
                    sleep_duration = RETRY_BASE_WAIT * (2 ** attempt)
                    time.sleep(sleep_duration)
                    continue
                else:
                    return {
                        "success": False,
                        "text": "",
                        "error": f"Quota limit reached after {MAX_RETRIES} retries. Wait and try again."
                    }
            else:
                # Step 5: On any other exception
                return {
                    "success": False,
                    "text": "",
                    "error": str(e)
                }

    return {
        "success": False,
        "text": "",
        "error": f"Quota limit reached after {MAX_RETRIES} retries. Wait and try again."
    }

def health_check() -> Dict[str, Any]:
    """
    Test both models are reachable before starting any investigation.

    Returns:
        Dict[str, Any]: Health status details.
    """
    # Call call_text_model using TEXT_MODEL
    text_res = call_text_model("Reply with exactly the word: OK")
    text_model_ok = text_res.get("success") is True

    # 1x1 transparent PNG in base64
    transparent_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    
    # Call call_vision_model using VISION_MODEL
    vision_res = call_vision_model("Describe this image.", transparent_png_b64, "image/png")
    vision_model_ok = vision_res.get("success") is True

    is_healthy = text_model_ok and vision_model_ok

    return {
        "vision_model_ok": vision_model_ok,
        "text_model_ok": text_model_ok,
        "vision_model": VISION_MODEL,
        "text_model": TEXT_MODEL,
        "status": "healthy" if is_healthy else "degraded"
    }

def call_gemini(
    prompt: str,
    model_type: str = "text",
    response_schema: Any = None,
    image_data: Any = None
) -> Dict[str, Any]:
    """
    Compatibility wrapper matching the original call_gemini signature.
    """
    import json
    if model_type == "vision" and image_data is not None:
        import io
        from PIL import Image
        buffered = io.BytesIO()
        image_data.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        res = call_vision_model(prompt, img_str, "image/png")
    else:
        res = call_text_model(prompt)
        
    if res.get("success") is True:
        text_response = res.get("text", "")
        try:
            json_data = json.loads(text_response)
            return {
                "status": "success",
                "data": json_data
            }
        except Exception:
            return {
                "status": "success",
                "data": {"text": text_response}
            }
    else:
        return {
            "status": "error",
            "error_code": "GEMINI_API_FAILURE",
            "message": res.get("error", "Unknown API error")
        }

