from unittest.mock import patch, MagicMock
from app.agents.visual_forensics import analyse_image, analyze_image_forensics

@patch("app.agents.visual_forensics.load_and_validate_image")
@patch("app.agents.visual_forensics.extract_metadata")
@patch("app.agents.visual_forensics.encode_image_for_gemini")
@patch("app.agents.visual_forensics.call_vision_model")
@patch("app.agents.visual_forensics.write_audit_log")
def test_analyse_image_success(
    mock_write_audit_log: MagicMock,
    mock_call_vision_model: MagicMock,
    mock_encode_image_for_gemini: MagicMock,
    mock_extract_metadata: MagicMock,
    mock_load_and_validate_image: MagicMock
) -> None:
    """Tests the full analyse_image process with mocked utilities and model output."""
    mock_load_and_validate_image.return_value = {"valid": True, "format": "PNG", "size_bytes": 100}
    mock_extract_metadata.return_value = {
        "has_camera_make": True,
        "has_camera_model": True,
        "software": "Canon EOS Utility",
        "datetime_original": "2026:06:30",
        "has_gps": False,
        "editing_software_detected": False,
        "anomaly_flags": ["some_minor_flag"],
        "raw_metadata": {}
    }
    mock_encode_image_for_gemini.return_value = {"base64_data": "dummy_base64", "mime_type": "image/png"}
    
    mock_call_vision_model.return_value = {
        "success": True,
        "text": '{"checklist_results": [], "anomaly_count": 0, "manipulation_confidence": 10, "primary_indicators": [], "summary": "Looks clean"}',
        "error": None
    }

    res = analyse_image("dummy.png", "test-session-123")
    
    assert res["error"] is False
    assert "metadata_anomalies" in res
    assert res["metadata_anomalies"] == ["some_minor_flag"]
    # Check adjusted confidence calculation:
    # raw: 10
    # adjusted = int(10 * 0.70 + min(1 * 10, 30)) = int(7.0 + 10) = 17
    assert res["manipulation_confidence"] == 17
    mock_write_audit_log.assert_called_once()

@patch("app.agents.visual_forensics.load_and_validate_image")
def test_analyse_image_invalid(mock_load_and_validate_image: MagicMock) -> None:
    """Tests that analyse_image fails immediately on invalid image check."""
    mock_load_and_validate_image.return_value = {"valid": False, "error": "Invalid format."}
    
    res = analyse_image("dummy.txt", "session-invalid")
    assert res["error"] is True
    assert res["message"] == "Invalid format."
    assert res["manipulation_confidence"] == 0

# Image and Metadata Utilities Unit Tests
import os
from typing import Any
from app.tools.image_utils import load_and_validate_image, encode_image_for_gemini
from app.tools.metadata_extractor import extract_metadata

def test_load_and_validate_image_not_found() -> None:
    res = load_and_validate_image("nonexistent_image.png")
    assert res["valid"] is False
    assert "File not found" in res["error"]

def test_load_and_validate_image_unsupported_format(tmp_path: Any) -> None:
    invalid_file = os.path.join(tmp_path, "test.txt")
    with open(invalid_file, "w") as f:
        f.write("text content")
    res = load_and_validate_image(str(invalid_file))
    assert res["valid"] is False
    assert "Unsupported format" in res["error"]

def test_load_and_validate_image_success(tmp_path: Any) -> None:
    valid_file = os.path.join(tmp_path, "test.png")
    with open(valid_file, "wb") as f:
        f.write(b"dummy image data")
    res = load_and_validate_image(str(valid_file))
    assert res["valid"] is True
    assert res["format"] == "PNG"
    assert res["size_bytes"] == 16
    assert res["error"] is None

def test_encode_image_for_gemini(tmp_path: Any) -> None:
    test_file = os.path.join(tmp_path, "test.png")
    with open(test_file, "wb") as f:
        f.write(b"hello image")
    res = encode_image_for_gemini(str(test_file))
    assert res["mime_type"] == "image/png"
    assert res["base64_data"] == "aGVsbG8gaW1hZ2U="

def test_extract_metadata_invalid_file() -> None:
    res = extract_metadata("nonexistent_file.png")
    assert "metadata_unreadable" in res["anomaly_flags"]
    assert res["raw_metadata"] == {}
