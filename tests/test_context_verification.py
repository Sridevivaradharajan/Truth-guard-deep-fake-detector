from unittest.mock import patch, MagicMock
from app.agents.context_verification import verify_claim, verify_claims_context

@patch("app.agents.context_verification.screen_claim_text")
@patch("app.agents.context_verification.call_text_model")
@patch("app.agents.context_verification.search_web")
@patch("app.agents.context_verification.write_audit_log")
def test_verify_claim_success(
    mock_write_audit_log: MagicMock,
    mock_search_web: MagicMock,
    mock_call_text_model: MagicMock,
    mock_screen_claim_text: MagicMock
) -> None:
    """Tests the context verification agent workflow with mocked sub-claims and verification."""
    # 1. Screen claim
    mock_screen_claim_text.return_value = {"safe": True, "redacted_text": "Cleaned claim text"}
    
    # 2. Decompose sub-claims (first call to call_text_model)
    # 3. Verify sub-claims (subsequent calls to call_text_model)
    mock_call_text_model.side_effect = [
        # Decomposition response
        {
            "success": True,
            "text": '{"original_claim": "Cleaned claim text", "sub_claims": [{"id": 1, "sub_claim": "Sub 1", "search_query": "Query 1"}, {"id": 2, "sub_claim": "Sub 2", "search_query": "Query 2"}, {"id": 3, "sub_claim": "Sub 3", "search_query": "Query 3"}]}',
            "error": None
        },
        # Consolidated verification response
        {
            "success": True,
            "text": '{"verdicts": [{"sub_claim_id": 1, "verdict": "SUPPORTED", "confidence": 90, "evidence": "Source A confirms"}, {"sub_claim_id": 2, "verdict": "CONTRADICTED", "confidence": 80, "evidence": "Source B denies"}, {"sub_claim_id": 3, "verdict": "UNVERIFIABLE", "confidence": 0, "evidence": "No details"}]}',
            "error": None
        }
    ]
    
    # Mock search_web for each query
    mock_search_web.return_value = {
        "search_successful": True,
        "results": [{"title": "Source", "url": "https://example.com/site", "snippet": "text"}],
        "result_count": 1,
        "error": None
    }

    res = verify_claim("Simulated Claim", "session-verify-123")
    
    assert res["error"] is False
    assert res["verified_count"] == 1
    assert res["contradicted_count"] == 1
    assert res["unverifiable_count"] == 1
    
    # Expected confidence:
    # base = int((1 * 100 + 1 * 50) / 3) = int(150 / 3) = 50
    # penalty = 1 * 20 = 20
    # context_confidence = 50 - 20 = 30
    assert res["context_confidence"] == 30
    assert res["claim_integrity"] == "LOW"
    assert "https://example.com/site" in res["sources"]
    mock_write_audit_log.assert_called_once()

@patch("app.agents.context_verification.screen_claim_text")
def test_verify_claim_unsafe(mock_screen_claim_text: MagicMock) -> None:
    """Tests verify_claim returns early on unsafe screening."""
    mock_screen_claim_text.return_value = {"safe": False, "reason": "Prompt injection detected."}
    
    res = verify_claim("Unsafe claim", "session-unsafe")
    assert res["error"] is True
    assert res["reason"] == "Prompt injection detected."
    assert res["claim_integrity"] == "UNVERIFIABLE"

@patch("app.agents.context_verification.verify_claim")
def test_compatibility_wrapper(mock_verify_claim: MagicMock) -> None:
    """Tests verify_claims_context compatibility wrapper logic."""
    mock_verify_claim.return_value = {
        "error": False,
        "claim_integrity": "MEDIUM",
        "sub_claims": [
            {"sub_claim": "Sub 1", "verdict": "SUPPORTED", "evidence": "Yes"},
            {"sub_claim": "Sub 2", "verdict": "CONTRADICTED", "evidence": "No"}
        ],
        "sources": ["https://site.org"],
        "context_confidence": 65
    }

    res = verify_claims_context(["Claim 1"])
    assert res["status"] == "success"
    assert res["result"]["is_context_valid"] is True
    assert "https://site.org" in res["result"]["verification_sources"]
    assert res["result"]["contextual_score"] == 0.65

# Web Search MCP Unit Tests
import requests
from app.tools.web_search_mcp import search_web, search_multiple

@patch("app.tools.web_search_mcp.requests.get")
def test_search_web_success(mock_get: MagicMock) -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = """
    <a class="result__url" href="https://example.com/item">Title</a>
    <a class="result__snippet" href="https://example.com/item">Snippet content</a>
    """
    mock_get.return_value = mock_resp

    res = search_web("test query")
    assert res["search_successful"] is True
    assert res["result_count"] == 1
    assert res["results"][0]["title"] == "Title"
    assert "example.com" in res["results"][0]["url"]
    assert res["results"][0]["snippet"] == "Snippet content"

@patch("app.tools.web_search_mcp.requests.get")
def test_search_web_timeout(mock_get: MagicMock) -> None:
    mock_get.side_effect = requests.exceptions.Timeout("Timeout")
    
    res = search_web("test timeout")
    assert res["search_successful"] is False
    assert "Search timed out" in res["error"]

@patch("app.tools.web_search_mcp.search_web")
def test_search_multiple(mock_search_web: MagicMock) -> None:
    mock_search_web.return_value = {"search_successful": True, "results": []}
    
    res = search_multiple(["query1", "query2"])
    assert len(res) == 2
    assert res[0]["search_successful"] is True
    assert mock_search_web.call_count == 2
