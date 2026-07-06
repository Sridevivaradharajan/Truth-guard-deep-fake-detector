import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List

# Core utilities and agents
from app.utils.logger import get_logger
from app.utils.security import create_session, cleanup_session, write_audit_log
from app.utils.gemini_client import health_check
from app.agents import visual_forensics, context_verification, triage_report
from app.tools.image_utils import load_and_validate_image

logger = get_logger(__name__)

# NODE 1 — input_validation
def input_validation(image_path: str, claim_text: str) -> dict:
    """
    Validates input image path and claim text limits, then initializes the session.
    """
    # Validate image path/extensions
    val_res = load_and_validate_image(image_path)
    if val_res.get("valid") is False:
        return {"error": True, "message": val_res.get("error")}

    # Validate claim text limits
    if not claim_text or len(claim_text) > 500:
        return {"error": True, "message": "Claim text is empty or too long."}

    # Initialize session
    session_details = create_session(str(uuid.uuid4()))
    session_id = session_details["session_id"]
    session_dir = session_details["session_dir"]
    return {
        "session_id": session_id,
        "session_dir": session_dir,
        "image_path": image_path,
        "claim_text": claim_text,
        "error": False
    }

# NODE 2 — parallel_investigation
def parallel_investigation(session_id: str, session_dir: str, image_path: str, claim_text: str) -> dict:
    """
    Runs visual forensics first, then context verification sequentially to support visual grounding.
    """
    # 1. Run visual forensics first
    visual_results = visual_forensics.analyse_image(image_path, session_id)
    
    # 2. Extract visual summary if no error, otherwise empty
    visual_summary = ""
    if visual_results.get("error") is False:
        visual_summary = visual_results.get("summary", "")
        
    # 3. Run context verification with visual keywords
    context_results = context_verification.verify_claim(claim_text, session_id, visual_summary)

    # Log failures in audit log if errors occurred, but continue
    if visual_results.get("error") is True:
        write_audit_log(session_id, "visual_forensics_failed", {
            "error": visual_results.get("message", "Unknown visual forensics error")
        })
        
    if context_results.get("error") is True:
        write_audit_log(session_id, "context_verification_failed", {
            "error": context_results.get("reason") or context_results.get("message", "Unknown context verification error")
        })

    return {
        "visual_results": visual_results,
        "context_results": context_results
    }

# NODE 3 — triage_and_report
def triage_and_report(
    visual_results: dict,
    context_results: dict,
    claim_text: str,
    image_path: str,
    session_id: str,
    session_dir: str
) -> dict:
    """
    Consolidates findings and compiles the final triage report.
    """
    report = triage_report.generate_report(
        visual_results=visual_results,
        context_results=context_results,
        claim_text=claim_text,
        image_path=image_path,
        session_id=session_id,
        session_dir=session_dir
    )
    return report

# NODE 4 — output
def output(report: dict, session_id: str) -> dict:
    """
    Verifies output evidence bundle and cleans up session temporary files.
    """
    # Confirm evidence bundle path is non-empty string
    bundle_path = report.get("evidence_bundle_path", "")
    if not isinstance(bundle_path, str) or not bundle_path.strip():
        logger.warning("Evidence bundle path is empty or invalid.")
    elif os.path.exists(bundle_path):
        # Move the ZIP file out of the session folder to the session root directory
        # so that it survives cleanup_session(session_id).
        session_root = os.getenv("TRUTHGUARD_SESSION_DIR", "/tmp/truthguard")
        filename = os.path.basename(bundle_path)
        new_bundle_path = os.path.join(session_root, filename)
        try:
            import shutil
            # Ensure session root directory exists
            os.makedirs(session_root, exist_ok=True)
            shutil.move(bundle_path, new_bundle_path)
            report["evidence_bundle_path"] = new_bundle_path
        except Exception as e:
            logger.error(f"Failed to move evidence bundle: {str(e)}")

    # Cleanup temporary session files
    cleanup_session(session_id)
    return report


# Entry point investigate function
def investigate(image_path: str, claim_text: str) -> dict:
    """
    Entrypoint to execute the full TruthGuard verification graph workflow.

    Args:
        image_path: Path to the image file to verify.
        claim_text: Statement/claim regarding the image.

    Returns:
        dict: The compiled investigation report, or error status.
    """
    try:
        # NODE 1: Validation
        node1_res = input_validation(image_path, claim_text)
        if node1_res.get("error") is True:
            return {"error": True, "message": node1_res.get("message")}

        session_id = node1_res["session_id"]
        session_dir = node1_res["session_dir"]

        # NODE 2: Parallel Investigation
        node2_res = parallel_investigation(
            session_id=session_id,
            session_dir=session_dir,
            image_path=image_path,
            claim_text=claim_text
        )
        if node2_res["visual_results"].get("error") is True:
            cleanup_session(session_id)
            return {"error": True, "message": node2_res["visual_results"].get("message", "Visual forensics failed.")}
        if node2_res["context_results"].get("error") is True:
            cleanup_session(session_id)
            return {"error": True, "message": node2_res["context_results"].get("reason") or node2_res["context_results"].get("message", "Context verification failed.")}

        # NODE 3: Triage & Report compiling
        report = triage_and_report(
            visual_results=node2_res["visual_results"],
            context_results=node2_res["context_results"],
            claim_text=claim_text,
            image_path=image_path,
            session_id=session_id,
            session_dir=session_dir
        )

        # NODE 4: Cleanup & Output
        final_report = output(report, session_id)
        return final_report

    except Exception as e:
        return {"error": True, "message": f"TruthGuard coordination workflow failed: {str(e)}"}

# Legacy compatibility wrapper
def run_triage(image_path: str, claims: List[str]) -> Dict[str, Any]:
    """
    Compatibility wrapper matching the original run_triage signature.
    """
    combined_claim = " | ".join(claims) if claims else "No claim submitted"
    res = investigate(image_path, combined_claim)
    if res.get("error") is True:
        return {
            "status": "error",
            "error_code": "COORDINATOR_TRIAGE_EXCEPTION",
            "message": res.get("message", "Triage execution failed.")
        }
    
    # Structure the dictionary to match expectations of legacy schemas
    return {
        "status": "success",
        "report": {
            "session_id": res.get("session_id"),
            "overall_trust_score": res.get("context_confidence", 0) / 100.0,
            "visual_forensics": {
                "is_altered": res.get("visual_manipulation_confidence", 0) > 50,
                "confidence_score": res.get("visual_manipulation_confidence", 0) / 100.0,
                "forgery_indicators": res.get("visual_primary_indicators", []),
                "metadata_summary": {},
                "notes": res.get("visual_summary", "")
            },
            "context_verification": {
                "is_context_valid": res.get("claim_integrity") in ("HIGH", "MEDIUM"),
                "claims_analyzed": claims,
                "verification_sources": res.get("context_sources", []),
                "discrepancies": [],
                "contextual_score": res.get("context_confidence", 0) / 100.0
            },
            "verdict": "VERIFIED" if res.get("risk_level") == "Low" else "SUSPICIOUS" if res.get("risk_level") == "Medium" else "FALSIFIED",
            "summary": res.get("visual_summary", "")
        }
    }

# ADK 2.0 Integration
from google.adk.agents.llm_agent import Agent
from google.adk.apps import App
from google.adk.tools import google_search

root_agent = Agent(
    model=os.getenv("TRUTHGUARD_TEXT_MODEL", "gemini-2.5-flash-lite"),
    name="coordinator_agent",
    description="TruthGuard forensic triage coordinator agent.",
    instruction="Coordinate visual forensics and context verification.",
    tools=[google_search],
)

app = App(
    name="truthguard",
    root_agent=root_agent,
)
