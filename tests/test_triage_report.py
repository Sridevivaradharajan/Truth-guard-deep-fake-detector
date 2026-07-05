import os
from typing import Any
from unittest.mock import patch, MagicMock
from app.agents.triage_report import compile_triage_report, export_to_pdf, generate_report
from app.models.report_schema import InvestigationReport
from app.tools.evidence_bundle import create_evidence_bundle

@patch("app.agents.triage_report.call_gemini")
def test_compile_triage_report_workflow(mock_call_gemini: MagicMock) -> None:
    """Tests the triage report compiler agent."""
    mock_call_gemini.return_value = {
        "status": "success",
        "data": {
            "session_id": "test-session-123",
            "overall_trust_score": 0.9,
            "visual_forensics": {
                "is_altered": False,
                "confidence_score": 0.9,
                "forgery_indicators": [],
                "metadata_summary": {},
                "notes": "Clean image"
            },
            "context_verification": {
                "is_context_valid": True,
                "claims_analyzed": ["claim"],
                "verification_sources": ["http://src"],
                "discrepancies": [],
                "contextual_score": 0.9
            },
            "verdict": "VERIFIED",
            "summary": "Verification succeeded."
        }
    }

    res = compile_triage_report("test-session-123", {}, {})
    assert res["status"] == "success"
    assert res["result"]["verdict"] == "VERIFIED"

def test_export_to_pdf_generation(tmp_path: Any) -> None:
    """Tests that a PDF file can be generated from the report data."""
    report_data = {
        "session_id": "pdf-session-999",
        "verdict": "SUSPICIOUS",
        "overall_trust_score": 0.45,
        "summary": "The image shows signs of splice editing and discrepancies in metadata."
    }
    
    pdf_path = os.path.join(tmp_path, "test_report.pdf")
    res = export_to_pdf(report_data, pdf_path)
    
    assert res["status"] == "success"
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0

def test_investigation_report_format() -> None:
    """Tests properties, dict output, and formatting layout of InvestigationReport."""
    report = InvestigationReport(
        session_id="test-session-xyz",
        timestamp="2026-06-30T12:00:00Z",
        claim_submitted="Sample claim statement",
        visual_manipulation_confidence=85,
        visual_anomaly_count=2,
        visual_primary_indicators=["lighting_direction", "hand_anatomy"],
        visual_summary="Visual indicators show splicing.",
        metadata_anomalies=["missing_camera_info"],
        context_verified_count=2,
        context_contradicted_count=1,
        context_unverifiable_count=0,
        context_confidence=50,
        context_sources=["https://example.com/site1", "https://example.com/site2"],
        harm_category="misinformation",
        harm_severity_score=60,
        risk_level="MEDIUM",
        recommended_action="Flag and review claim context.",
        evidence_bundle_path=""
    )
    
    report_dict = report.to_dict()
    assert report_dict["session_id"] == "test-session-xyz"
    assert report_dict["visual_manipulation_confidence"] == 85
    
    report_text = report.to_report_text()
    assert "TRUTHGUARD INVESTIGATION REPORT" in report_text
    assert "Session ID     : test-session-xyz" in report_text
    assert "Verified       : 2 of 3 sub-claims" in report_text
    assert "Contradicted   : 1 of 3 sub-claims" in report_text
    assert "  https://example.com/site1" in report_text

def test_create_evidence_bundle_success(tmp_path: Any) -> None:
    """Tests the evidence bundle creation flow including zip creation."""
    report = InvestigationReport(
        session_id="test-session-xyz",
        timestamp="2026-06-30T12:00:00Z",
        claim_submitted="Sample claim statement",
        visual_manipulation_confidence=85,
        visual_anomaly_count=2,
        visual_primary_indicators=["lighting_direction", "hand_anatomy"],
        visual_summary="Visual indicators show splicing.",
        metadata_anomalies=["missing_camera_info"],
        context_verified_count=2,
        context_contradicted_count=1,
        context_unverifiable_count=0,
        context_confidence=50,
        context_sources=["https://example.com/site1", "https://example.com/site2"],
        harm_category="misinformation",
        harm_severity_score=60,
        risk_level="MEDIUM",
        recommended_action="Flag and review claim context.",
        evidence_bundle_path=""
    )
    
    # Create a dummy image
    image_file = os.path.join(tmp_path, "test.png")
    with open(image_file, "wb") as f:
        f.write(b"dummy image data")
        
    session_dir = os.path.join(tmp_path, "session_xyz")
    os.makedirs(session_dir, exist_ok=True)
    
    zip_path = create_evidence_bundle(report, image_file, session_dir)
    assert os.path.exists(zip_path)
    assert zip_path.endswith(".zip")

@patch("app.agents.triage_report.call_text_model")
@patch("app.agents.triage_report.create_evidence_bundle")
@patch("app.agents.triage_report.write_audit_log")
def test_generate_report_success(
    mock_write_audit_log: MagicMock,
    mock_create_evidence_bundle: MagicMock,
    mock_call_text_model: MagicMock
) -> None:
    """Tests generate_report risk classification and severity math."""
    mock_call_text_model.return_value = {
        "success": True,
        "text": '{"harm_category": "Political Misinformation", "reasoning": "Reason here"}'
    }
    mock_create_evidence_bundle.return_value = "/path/to/evidence.zip"
    
    visual = {
        "manipulation_confidence": 80,
        "anomaly_count": 3,
        "primary_indicators": ["hand_anatomy"],
        "summary": "AI generated hand details",
        "metadata_anomalies": ["missing_camera_info"]
    }
    
    context = {
        "verified_count": 1,
        "contradicted_count": 2,
        "unverifiable_count": 1,
        "context_confidence": 35,
        "sources": ["https://source.com"]
    }

    res = generate_report(
        visual_results=visual,
        context_results=context,
        claim_text="Political claim details",
        image_path="test_image.png",
        session_id="session-triage-777",
        session_dir="/tmp/session"
    )
    
    assert res["session_id"] == "session-triage-777"
    assert res["harm_category"] == "Political Misinformation"
    assert res["evidence_bundle_path"] == "/path/to/evidence.zip"
    
    # Calculation check:
    # visual_component = 80 * 0.3 = 24.0
    # context_component = (2 * 15) * 0.25 = 30 * 0.25 = 7.5
    # category_component = 85 * 0.25 = 21.25
    # spread_component = 50 * 0.2 = 10.0
    # sum = 24.0 + 7.5 + 21.25 + 10.0 = 62.75 -> int(62.75) = 62
    assert res["harm_severity_score"] == 62
    assert res["risk_level"] == "High"
    mock_write_audit_log.assert_called_once()
