import os
import re
import shutil
import datetime
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

# Pre-compiled regular expressions for PII detection
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
AADHAAR_PATTERN = re.compile(r'\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b')
PHONE_PATTERN = re.compile(r'\b\d{10,}\b')
BANK_ACCOUNT_PATTERN = re.compile(r'\b\d{9,18}\b')
NAME_PATTERN = re.compile(r'\b(?:Mr|Mrs|Ms|Dr)\.?\s+[A-Z][a-zA-Z]*\b')

PROMPT_INJECTION_KEYWORDS = [
    "ignore previous instructions",
    "you are now",
    "disregard your instructions",
    "new persona",
    "act as",
    "forget your rules"
]

def screen_claim_text(text: str) -> Dict[str, Any]:
    """
    Detects prompt injection patterns and redacts PII (emails, phone numbers,
    Aadhaar numbers, bank accounts, and names preceded by titles) from text.

    Args:
        text: The raw claim text.

    Returns:
        Dict[str, Any]: Structured screening result.
    """
    # 1. Detect prompt injection
    lower_text = text.lower()
    for keyword in PROMPT_INJECTION_KEYWORDS:
        if keyword in lower_text:
            return {
                "safe": False,
                "redacted_text": "",
                "flags": ["prompt_injection"],
                "reason": "Prompt injection pattern detected in claim text."
            }

    # 2. Redact PII (Order matters to prevent regex overlapping issues)
    try:
        redacted = text
        redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", redacted)
        redacted = AADHAAR_PATTERN.sub("[REDACTED_AADHAAR]", redacted)
        redacted = PHONE_PATTERN.sub("[REDACTED_PHONE]", redacted)
        redacted = BANK_ACCOUNT_PATTERN.sub("[REDACTED_BANK_ACCOUNT]", redacted)
        redacted = NAME_PATTERN.sub("[REDACTED_NAME]", redacted)
        
        return {
            "safe": True,
            "redacted_text": redacted,
            "flags": [],
            "reason": ""
        }
    except Exception as e:
        return {
            "safe": False,
            "redacted_text": "",
            "flags": ["pii_screening_error"],
            "reason": f"An error occurred during PII screening: {str(e)}"
        }

def screen_image_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Removes location-sensitive metadata keys from the image metadata dictionary.

    Args:
        metadata: The raw metadata dictionary.

    Returns:
        Dict[str, Any]: Sanitised metadata and list of removed keys.
    """
    sanitised_metadata: Dict[str, Any] = {}
    removed_fields: List[str] = []
    
    sensitive_keywords = ["gps", "latitude", "longitude", "location"]
    
    for key, value in metadata.items():
        key_lower = key.lower()
        if any(keyword in key_lower for keyword in sensitive_keywords):
            removed_fields.append(key)
        else:
            sanitised_metadata[key] = value
            
    return {
        "sanitised_metadata": sanitised_metadata,
        "removed_fields": removed_fields
    }

def create_session(session_id: str) -> Dict[str, Any]:
    """
    Creates the session directory and the evidence subdirectory.

    Args:
        session_id: Unique session identifier.

    Returns:
        Dict[str, Any]: Session details.
    """
    session_root = os.getenv("TRUTHGUARD_SESSION_DIR", "/tmp/truthguard")
    session_dir = os.path.join(session_root, session_id)
    evidence_dir = os.path.join(session_dir, "evidence")
    
    os.makedirs(evidence_dir, exist_ok=True)
    
    created_at = datetime.datetime.utcnow().isoformat() + "Z"
    
    return {
        "session_id": session_id,
        "session_dir": session_dir,
        "created_at": created_at
    }

def cleanup_session(session_id: str) -> Dict[str, Any]:
    """
    Recursively deletes the session directory and all its contents.

    Args:
        session_id: Unique session identifier.

    Returns:
        Dict[str, Any]: Structured cleanup status.
    """
    session_root = os.getenv("TRUTHGUARD_SESSION_DIR", "/tmp/truthguard")
    session_dir = os.path.join(session_root, session_id)
    
    try:
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        return {
            "deleted": True,
            "session_id": session_id
        }
    except Exception as e:
        return {
            "deleted": False,
            "session_id": session_id,
            "error": str(e)
        }

def write_audit_log(session_id: str, event: str, details: Dict[str, Any]) -> None:
    """
    Appends a JSON line to the audit log for the session.

    Args:
        session_id: Unique session identifier.
        event: Event name.
        details: Additional context details.
    """
    session_root = os.getenv("TRUTHGUARD_SESSION_DIR", "/tmp/truthguard")
    session_dir = os.path.join(session_root, session_id)
    log_path = os.path.join(session_dir, "audit.log")
    
    try:
        # Ensure session directory exists before writing logs
        os.makedirs(session_dir, exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "session_id": session_id,
            "event": event,
            "details": details
        }
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        # Silent failure to ensure no raw exception is raised
        pass

def scrub_pii(text: str) -> str:
    """
    Compatibility wrapper to scrub PII from text.

    Args:
        text: Raw text string.

    Returns:
        str: Redacted text string.
    """
    res = screen_claim_text(text)
    if res.get("safe") is True:
        return res["redacted_text"]
    return f"[ERROR: {res['reason']}]"

def screen_input(raw_input: str) -> Dict[str, Any]:
    """
    Compatibility wrapper to screen inputs.

    Args:
        raw_input: Raw input string.

    Returns:
        Dict[str, Any]: Structured screening results.
    """
    res = screen_claim_text(raw_input)
    if res.get("safe") is True:
        return {
            "status": "success",
            "scrubbed_text": res["redacted_text"]
        }
    return {
        "status": "error",
        "error_code": "PROMPT_INJECTION_DETECTED",
        "message": res["reason"]
    }

