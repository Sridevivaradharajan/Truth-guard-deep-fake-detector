from unittest.mock import patch, MagicMock
from app.utils.gemini_client import call_text_model, call_vision_model, health_check, call_gemini

@patch("google.generativeai.GenerativeModel")
@patch("time.sleep")
def test_call_text_model_success(mock_sleep: MagicMock, mock_model_class: MagicMock) -> None:
    """Tests that call_text_model returns success=True for a simple prompt."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "OK"
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model

    res = call_text_model("Simple prompt")
    
    assert res["success"] is True
    assert res["text"] == "OK"
    assert res["error"] is None

@patch("google.generativeai.GenerativeModel")
@patch("time.sleep")
def test_call_text_model_invalid_api_key(mock_sleep: MagicMock, mock_model_class: MagicMock) -> None:
    """Tests that call_text_model returns success=False with structured error when API key is invalid."""
    mock_model = MagicMock()
    # Mocking standard API key validation failure exception
    mock_model.generate_content.side_effect = Exception("API_KEY_INVALID: The provided API key is invalid.")
    mock_model_class.return_value = mock_model

    res = call_text_model("Simple prompt")
    
    assert res["success"] is False
    assert res["text"] == ""
    assert "API_KEY_INVALID" in res["error"]

@patch("google.generativeai.GenerativeModel")
@patch("time.sleep")
def test_health_check_healthy_status(mock_sleep: MagicMock, mock_model_class: MagicMock) -> None:
    """Tests that health_check returns status='healthy' when both models respond successfully."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "OK"
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model

    res = health_check()
    
    assert res["status"] == "healthy"
    assert res["text_model_ok"] is True
    assert res["vision_model_ok"] is True

@patch("google.generativeai.GenerativeModel")
@patch("time.sleep")
def test_call_gemini_compatibility_wrapper(mock_sleep: MagicMock, mock_model_class: MagicMock) -> None:
    """Tests that the call_gemini compatibility wrapper delegates correctly and returns status='success'."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"verdict": "VERIFIED"}'
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model

    res = call_gemini("Check this")
    assert res["status"] == "success"
    assert res["data"]["verdict"] == "VERIFIED"
