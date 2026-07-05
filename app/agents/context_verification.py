import json
from typing import Dict, Any, List
from app.utils.gemini_client import call_text_model
from app.utils.security import screen_claim_text, write_audit_log
from app.tools.web_search_mcp import search_web

def verify_claim(claim_text: str, session_id: str, visual_keywords: str = "") -> Dict[str, Any]:
    """
    Decomposes, searches, and verifies sub-claims of a claim against web evidence.
    Optimized to run consolidated verification in a single API call and leverage visual description.

    Args:
        claim_text: The statement/claim to verify.
        session_id: Unique session identifier.
        visual_keywords: Extracted visual description or keywords from image analysis.

    Returns:
        Dict[str, Any]: Verification verdict and sub-claim analysis results.
    """
    try:
        # Step 1 — Security screening
        screening_res = screen_claim_text(claim_text)
        if screening_res["safe"] is False:
            return {
                "error": True,
                "reason": screening_res["reason"],
                "context_confidence": 0,
                "sub_claims": [],
                "verified_count": 0,
                "contradicted_count": 0,
                "unverifiable_count": 0,
                "sources": [],
                "claim_integrity": "UNVERIFIABLE"
            }
        
        redacted_text = screening_res["redacted_text"]

        # Step 2 — Claim decomposition via call_text_model
        visual_info_str = f"\nAlso, target the origin and context of the photo itself using these visual details: {visual_keywords}" if visual_keywords else ""
        
        decomp_prompt = f"""
You are a professional fact-checking analyst.
Break the following claim into between 3 and 5 independent, searchable sub-claims.
Each sub-claim must be a single verifiable statement confirmable by a web search.{visual_info_str}
Do not produce more than 5 or fewer than 3 sub-claims.
Return valid JSON only. No preamble. No markdown fences.

Claim: {redacted_text}

{{
  "original_claim": "full original claim",
  "sub_claims": [
    {{"id": 1, "sub_claim": "verifiable statement", "search_query": "web search query"}}
  ]
}}
"""
        decomp_res = call_text_model(decomp_prompt)
        if decomp_res["success"] is False:
            return {
                "error": True,
                "reason": decomp_res["error"],
                "context_confidence": 0,
                "sub_claims": [],
                "verified_count": 0,
                "contradicted_count": 0,
                "unverifiable_count": 0,
                "sources": [],
                "claim_integrity": "UNVERIFIABLE"
            }

        decomp_text = decomp_res["text"].strip()
        if decomp_text.startswith("```"):
            lines = decomp_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            decomp_text = "\n".join(lines).strip()

        try:
            decomp_data = json.loads(decomp_text)
        except json.JSONDecodeError:
            return {
                "error": True,
                "reason": "Decomposition response was not valid JSON.",
                "context_confidence": 0,
                "sub_claims": [],
                "verified_count": 0,
                "contradicted_count": 0,
                "unverifiable_count": 0,
                "sources": [],
                "claim_integrity": "UNVERIFIABLE"
            }

        sub_claims = decomp_data.get("sub_claims", [])
        if not sub_claims:
            return {
                "error": True,
                "reason": "Decomposition response had no sub-claims.",
                "context_confidence": 0,
                "sub_claims": [],
                "verified_count": 0,
                "contradicted_count": 0,
                "unverifiable_count": 0,
                "sources": [],
                "claim_integrity": "UNVERIFIABLE"
            }

        # Step 3 & 4 — Search each sub-claim independently and compile search evidence
        sub_claims_evidence = []
        unique_urls = set()

        for sc in sub_claims:
            sc_id = sc.get("id")
            sc_text = sc.get("sub_claim")
            sc_query = sc.get("search_query")

            # Call search_web separately for each sub-claim
            search_res = search_web(sc_query)
            
            results = []
            if search_res.get("search_successful") is True:
                results = search_res.get("results", [])
                for r in results:
                    if r.get("url"):
                        unique_urls.add(r["url"])

            sub_claims_evidence.append({
                "id": sc_id,
                "sub_claim": sc_text,
                "search_results": results
            })

        # Make a single, consolidated API call to verify all sub-claims at once
        verify_prompt = f"""
You are a factual verification system.
Analyse the following sub-claims against their respective search results.
For each sub-claim, determine if the evidence supports, contradicts, or leaves it unverifiable.

CRITICAL GROUNDING RULES:
1. If a sub-claim asserts a massive, public, real-world fact or event (e.g. a floating city in Mumbai, a public official statement, a major disaster) and the search results contain NO reputable news reports confirming it actually happened, you MUST label it CONTRADICTED or UNVERIFIABLE.
2. Do NOT treat conceptual proposals, design renders, satirical articles, or speculative designs as SUPPORTED evidence for the claim that the event actually happened.
3. If search results are empty, the verdict must be UNVERIFIABLE.

Sub-claims and search evidence:
{json.dumps(sub_claims_evidence, indent=2)}

Return valid JSON only. No preamble. No markdown fences.
Respond with the following format:
{{
  "verdicts": [
    {{
      "sub_claim_id": 1,
      "verdict": "SUPPORTED or CONTRADICTED or UNVERIFIABLE",
      "confidence": 0-100,
      "evidence": "one sentence citing the most relevant source"
    }}
  ]
}}
"""
        verify_res = call_text_model(verify_prompt)
        if verify_res.get("success") is False:
            return {
                "error": True,
                "reason": verify_res.get("error") or "Consolidated verification API call failed.",
                "context_confidence": 0,
                "sub_claims": [],
                "verified_count": 0,
                "contradicted_count": 0,
                "unverifiable_count": 0,
                "sources": [],
                "claim_integrity": "UNVERIFIABLE"
            }
        
        # Parse consolidated verdicts
        sub_claims_with_verdicts = []
        verified_count = 0
        contradicted_count = 0
        unverifiable_count = 0
        
        verdicts_map = {}
        verify_text = verify_res["text"].strip()
        if verify_text.startswith("```"):
            lines = verify_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            verify_text = "\n".join(lines).strip()
        try:
            parsed_verify = json.loads(verify_text)
            for v in parsed_verify.get("verdicts", []):
                sub_claim_id_key = v.get("sub_claim_id")
                if sub_claim_id_key is not None:
                    verdicts_map[str(sub_claim_id_key)] = v
        except Exception:
            pass

        for sc in sub_claims:
            sc_id = sc.get("id")
            sc_text = sc.get("sub_claim")
            
            v = verdicts_map.get(str(sc_id), {})
            verdict = v.get("verdict", "UNVERIFIABLE")
            confidence = v.get("confidence", 0)
            evidence = v.get("evidence", "No search results available or verification failed.")
            
            if verdict == "SUPPORTED":
                verified_count += 1
            elif verdict == "CONTRADICTED":
                contradicted_count += 1
            else:
                unverifiable_count += 1

            sub_claims_with_verdicts.append({
                "id": sc_id,
                "sub_claim": sc_text,
                "verdict": verdict,
                "confidence": confidence,
                "evidence": evidence
            })

        # Step 5 — Aggregate results
        total_sub_claims = len(sub_claims)
        base = int((verified_count * 100 + unverifiable_count * 50) / total_sub_claims) if total_sub_claims > 0 else 0
        penalty = contradicted_count * 20
        context_confidence = max(0, min(100, base - penalty))

        if context_confidence >= 80:
            claim_integrity = "HIGH"
        elif context_confidence >= 50:
            claim_integrity = "MEDIUM"
        elif context_confidence >= 20:
            claim_integrity = "LOW"
        else:
            claim_integrity = "UNVERIFIABLE"

        # Step 6 — Audit and return
        write_audit_log(session_id, "context_verification_complete", {
            "verified": verified_count,
            "contradicted": contradicted_count,
            "confidence": context_confidence
        })

        return {
            "sub_claims": sub_claims_with_verdicts,
            "verified_count": verified_count,
            "contradicted_count": contradicted_count,
            "unverifiable_count": unverifiable_count,
            "context_confidence": context_confidence,
            "sources": sorted(list(unique_urls)),
            "claim_integrity": claim_integrity,
            "error": False
        }

    except Exception as e:
        return {
            "error": True,
            "reason": f"An unexpected error occurred in context verification agent: {str(e)}",
            "context_confidence": 0,
            "sub_claims": [],
            "verified_count": 0,
            "contradicted_count": 0,
            "unverifiable_count": 0,
            "sources": [],
            "claim_integrity": "UNVERIFIABLE"
        }

def verify_claims_context(claims: List[str]) -> Dict[str, Any]:
    """
    Compatibility wrapper matching the original verify_claims_context signature.
    """
    if not claims:
        return {
            "status": "success",
            "result": {
                "is_context_valid": True,
                "claims_analyzed": [],
                "verification_sources": [],
                "discrepancies": [],
                "contextual_score": 1.0
            }
        }
    
    combined_claim = " | ".join(claims)
    res = verify_claim(combined_claim, "compatibility-session")
    if res.get("error") is False:
        is_valid = res.get("claim_integrity") in ("HIGH", "MEDIUM")
        discrepancies = [
            f"{s['sub_claim']}: {s['verdict']} ({s['evidence']})" 
            for s in res.get("sub_claims", []) 
            if s.get("verdict") != "SUPPORTED"
        ]
        return {
            "status": "success",
            "result": {
                "is_context_valid": is_valid,
                "claims_analyzed": claims,
                "verification_sources": res.get("sources", []),
                "discrepancies": discrepancies,
                "contextual_score": res.get("context_confidence", 0) / 100.0
            }
        }
    
    return {
        "status": "error",
        "error_code": "CONTEXT_VERIFICATION_FAILED",
        "message": res.get("reason", "Verification failed.")
    }
