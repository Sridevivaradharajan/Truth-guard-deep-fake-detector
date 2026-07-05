import os
from unittest.mock import patch, MagicMock
from app.agents.coordinator import investigate, run_triage

@patch("app.agents.coordinator.load_and_validate_image")
@patch("app.agents.coordinator.create_session")
@patch("app.agents.coordinator.visual_forensics.analyse_image")
@patch("app.agents.coordinator.context_verification.verify_claim")
@patch("app.agents.coordinator.triage_report.generate_report")
@patch("app.agents.coordinator.cleanup_session")
def test_investigate_success(
    mock_cleanup_session: MagicMock,
    mock_generate_report: MagicMock,
    mock_verify_claim: MagicMock,
    mock_analyse_image: MagicMock,
    mock_create_session: MagicMock,
    mock_load_and_validate_image: MagicMock
) -> None:
    # Set up mocks
    mock_load_and_validate_image.return_value = {"valid": True, "format": "PNG", "size_bytes": 100}
    mock_create_session.return_value = {"session_id": "session-xyz-123", "session_dir": "/tmp/session-xyz-123"}
    
    mock_analyse_image.return_value = {"manipulation_confidence": 10, "error": False}
    mock_verify_claim.return_value = {"context_confidence": 90, "error": False}
    
    mock_generate_report.return_value = {
        "session_id": "session-xyz-123",
        "evidence_bundle_path": "/tmp/session-xyz-123/bundle.zip",
        "risk_level": "Low",
        "context_confidence": 90,
        "visual_manipulation_confidence": 10
    }

    res = investigate("image.png", "Sample claim text here")
    
    assert res.get("error", False) is False
    assert res["session_id"] == "session-xyz-123"
    assert res["evidence_bundle_path"] == "/tmp/session-xyz-123/bundle.zip"
    
    # Assert nodes and edges execution sequence
    mock_load_and_validate_image.assert_called_once_with("image.png")
    mock_create_session.assert_called_once()
    mock_analyse_image.assert_called_once_with("image.png", "session-xyz-123")
    mock_verify_claim.assert_called_once_with("Sample claim text here", "session-xyz-123", "")
    mock_cleanup_session.assert_called_once_with("session-xyz-123")

@patch("app.agents.coordinator.load_and_validate_image")
def test_investigate_validation_failure(mock_load_and_validate_image: MagicMock) -> None:
    # Set up validation mock to fail
    mock_load_and_validate_image.return_value = {"valid": False, "error": "File not found."}

    res = investigate("nonexistent.png", "Claim text")
    
    assert res["error"] is True
    assert "File not found." in res["message"]

@patch("app.agents.coordinator.load_and_validate_image")
def test_investigate_claim_too_long(mock_load_and_validate_image: MagicMock) -> None:
    mock_load_and_validate_image.return_value = {"valid": True, "format": "PNG", "size_bytes": 100}
    # Too long claim (500 chars limit)
    too_long_claim = "A" * 501
    res = investigate("image.png", too_long_claim)
    
    assert res["error"] is True
    assert "Claim text is empty or too long." in res["message"]

@patch("app.agents.coordinator.investigate")
def test_run_triage_compatibility(mock_investigate: MagicMock) -> None:
    # Setup legacy return mock
    mock_investigate.return_value = {
        "session_id": "compat-session",
        "context_confidence": 75,
        "visual_manipulation_confidence": 20,
        "visual_primary_indicators": [],
        "visual_summary": "Notes here",
        "context_sources": ["http://source.org"],
        "risk_level": "Medium",
        "claim_integrity": "MEDIUM"
    }

    res = run_triage("image.png", ["Claim 1", "Claim 2"])
    
    assert res["status"] == "success"
    assert res["report"]["session_id"] == "compat-session"
    assert res["report"]["overall_trust_score"] == 0.75
    assert res["report"]["verdict"] == "SUSPICIOUS"
    mock_investigate.assert_called_once_with("image.png", "Claim 1 | Claim 2")
