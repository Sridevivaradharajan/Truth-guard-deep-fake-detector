import json
from typing import Dict, Any, List
from app.utils.gemini_client import call_vision_model
from app.utils.security import screen_image_metadata, write_audit_log
from app.tools.image_utils import load_and_validate_image, encode_image_for_gemini
from app.tools.metadata_extractor import extract_metadata

def analyse_image(image_path: str, session_id: str) -> Dict[str, Any]:
    """
    Runs visual forensics on an image: validates, extracts metadata, sanitises,
    encodes, calls Gemini Vision model, and merges metadata anomalies.

    Args:
        image_path: Path to the local image file.
        session_id: Unique session identifier.

    Returns:
        Dict[str, Any]: Forensics report or error details.
    """
    try:
        # Step 1 — Validate image
        validate_res = load_and_validate_image(image_path)
        if validate_res["valid"] is False:
            return {
                "error": True,
                "message": validate_res["error"],
                "manipulation_confidence": 0,
                "checklist_results": [],
                "anomaly_count": 0,
                "primary_indicators": [],
                "summary": "",
                "metadata_anomalies": []
            }

        # Step 2 — Extract and sanitise metadata
        metadata_res = extract_metadata(image_path)
        screen_image_metadata(metadata_res) # Sanitise location metadata before any logging

        # Step 3 — Encode image
        encoded = encode_image_for_gemini(image_path)
        if "error" in encoded:
            return {
                "error": True,
                "message": encoded["error"],
                "manipulation_confidence": 0,
                "checklist_results": [],
                "anomaly_count": 0,
                "primary_indicators": [],
                "summary": "",
                "metadata_anomalies": []
            }

        # Step 4 — Call Gemini Vision via gemini_client
        prompt = """
You are a digital forensics expert specialising in detecting AI-generated images.
Analyse the provided image against each of the following 7 checklist items.
For each item respond with exactly FLAGGED or CLEAR followed by one sentence of evidence.
Return valid JSON only. No preamble text. No markdown fences.

{
  "checklist_results": [
    {"item": "facial_geometry",        "status": "FLAGGED or CLEAR", "evidence": "one sentence"},
    {"item": "lighting_direction",     "status": "FLAGGED or CLEAR", "evidence": "one sentence"},
    {"item": "background_edges",       "status": "FLAGGED or CLEAR", "evidence": "one sentence"},
    {"item": "hand_anatomy",           "status": "FLAGGED or CLEAR", "evidence": "one sentence"},
    {"item": "compression_artifacts",  "status": "FLAGGED or CLEAR", "evidence": "one sentence"},
    {"item": "reflection_plausibility","status": "FLAGGED or CLEAR", "evidence": "one sentence"},
    {"item": "overall_coherence",      "status": "FLAGGED or CLEAR", "evidence": "one sentence"}
  ],
  "anomaly_count": <integer 0-7>,
  "manipulation_confidence": <integer 0-100>,
  "primary_indicators": ["most significant flagged item names"],
  "summary": "two sentence summary of findings"
}
"""
        result = call_vision_model(prompt, encoded["base64_data"], encoded["mime_type"])
        if result["success"] is False:
            # Retry once
            result = call_vision_model(prompt, encoded["base64_data"], encoded["mime_type"])
            if result["success"] is False:
                return {
                    "error": True,
                    "message": result["error"],
                    "manipulation_confidence": 0
                }

        # Step 5 — Parse JSON from result["text"]
        raw_text = result["text"].strip()
        
        # Clean markdown code block wraps if LLM accidentally outputs them
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_text = "\n".join(lines).strip()

        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            return {
                "error": True,
                "message": "Vision response was not valid JSON.",
                "manipulation_confidence": 0
            }

        # Step 6 — Merge metadata and recalculate confidence
        anomaly_flags = metadata_res.get("anomaly_flags", [])
        parsed["metadata_anomalies"] = anomaly_flags
        
        raw_confidence = parsed.get("manipulation_confidence", 0)
        adjusted = int(raw_confidence * 0.70 + min(len(anomaly_flags) * 10, 30))
        adjusted = max(0, min(100, adjusted))
        
        parsed["manipulation_confidence"] = adjusted

        # Step 7 — Audit log and return
        write_audit_log(session_id, "visual_forensics_complete", {
            "anomaly_count": parsed.get("anomaly_count", 0),
            "confidence": adjusted
        })
        
        parsed["error"] = False
        return parsed

    except Exception as e:
        return {
            "error": True,
            "message": f"An unexpected error occurred in visual forensics agent: {str(e)}",
            "manipulation_confidence": 0,
            "checklist_results": [],
            "anomaly_count": 0,
            "primary_indicators": [],
            "summary": "",
            "metadata_anomalies": []
        }

def analyze_image_forensics(image_path: str) -> Dict[str, Any]:
    """
    Compatibility wrapper matching the original analyze_image_forensics signature.
    """
    res = analyse_image(image_path, "default-compatibility-session")
    if res.get("error") is False:
        return {
            "status": "success",
            "result": res
        }
    return {
        "status": "error",
        "error_code": "VISUAL_FORENSICS_FAILED",
        "message": res.get("message", "Forensics validation failed.")
    }
