import json
import datetime
from typing import Dict, Any
from app.utils.gemini_client import call_text_model, call_gemini
from app.utils.security import write_audit_log
from app.models.report_schema import InvestigationReport
from app.tools.evidence_bundle import create_evidence_bundle

def generate_report(
    visual_results: dict,
    context_results: dict,
    claim_text: str,
    image_path: str,
    session_id: str,
    session_dir: str
) -> dict:
    """
    Triage and Report Agent main entrypoint.
    Determines harm category, calculates severity score, evaluates risk levels,
    generates evidence zip/pdf bundles, and records audit logs.

    Args:
        visual_results: Output dictionary from visual forensics agent.
        context_results: Output dictionary from context verification agent.
        claim_text: The original user claim.
        image_path: Path to the original verified image file.
        session_id: Session identifier.
        session_dir: Directory path for the active session.

    Returns:
        dict: Plain dictionary representation of the InvestigationReport.
    """
    try:
        # Step 1 — Classify harm category via call_text_model
        prompt = f"""
You are a content risk analyst. Based on the findings below, classify the harm category.
Visual findings: {json.dumps(visual_results)}
Context findings: {json.dumps(context_results)}
Original claim: {claim_text}

Choose EXACTLY ONE from this list:
  "Political Misinformation" — targets electoral processes, political figures, or public policy
  "Financial Fraud" — designed to impersonate institutions or individuals for monetary gain
  "Identity Impersonation" — uses a real person's likeness without their consent
  "Public Safety Risk" — could trigger panic, communal tension, or physical harm
  "Entertainment / Low Risk" — satirical or clearly synthetic with no harm vector

Return JSON only. No preamble. No markdown fences.
{{"harm_category": "exact string from list", "reasoning": "two sentences maximum"}}
"""
        harm_res = call_text_model(prompt)
        
        harm_category = "Entertainment / Low Risk"
        if harm_res.get("success") is True:
            raw_text = harm_res["text"].strip()
            # Clean markdown code block wraps if LLM accidentally outputs them
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()
            try:
                parsed_harm = json.loads(raw_text)
                harm_category = parsed_harm.get("harm_category", "Entertainment / Low Risk")
            except Exception:
                pass

        # Step 2 — Calculate harm severity score
        category_weights = {
            "Public Safety Risk": 90,
            "Political Misinformation": 85,
            "Financial Fraud": 80,
            "Identity Impersonation": 70,
            "Entertainment / Low Risk": 10
        }
        
        visual_component = visual_results.get("manipulation_confidence", 0) * 0.30
        context_component = (context_results.get("contradicted_count", 0) * 15) * 0.25
        category_component = category_weights.get(harm_category, 50) * 0.25
        spread_component = 50 * 0.20
        
        harm_severity_score = max(0, min(100, int(
            visual_component + context_component + category_component + spread_component
        )))

        # HEURISTIC OVERRIDE:
        # If visual manipulation is significant (>= 50%) and context verification is weak or contradicted,
        # we escalate the harm category from low-risk to a higher category.
        is_suspicious_synthetic = (
            visual_results.get("manipulation_confidence", 0) >= 50 and 
            (context_results.get("context_confidence", 100) < 60 or context_results.get("contradicted_count", 0) > 0)
        )
        if is_suspicious_synthetic and harm_category == "Entertainment / Low Risk":
            claim_lower = claim_text.lower()
            if any(kw in claim_lower for kw in ["bank", "money", "upi", "fraud", "scam", "official", "finance", "pay"]):
                harm_category = "Financial Fraud"
            elif any(kw in claim_lower for kw in ["riot", "police", "fire", "danger", "hazard", "threat", "bomb", "panic"]):
                harm_category = "Public Safety Risk"
            else:
                harm_category = "Political Misinformation"
                
            category_component = category_weights.get(harm_category, 50) * 0.25
            harm_severity_score = max(61, min(100, int(
                visual_component + context_component + category_component + spread_component + 15
            )))

        # Step 3 — Assign risk level and recommended action
        if harm_severity_score <= 30:
            risk_level = "Low"
            if visual_results.get("manipulation_confidence", 0) >= 50:
                action = "This content may be AI-generated. Label it as synthetic before sharing. No urgent action is required."
            else:
                action = "This content appears authentic. No signs of visual manipulation or context discrepancies detected. No action required."
        elif harm_severity_score <= 60:
            risk_level = "Medium"
            action = "Flag this content for human review. Do not distribute without independent verification from a trusted source."
        elif harm_severity_score <= 80:
            risk_level = "High"
            action = "Report this content to the platform using their synthetic media policy. Preserve the evidence bundle. Consider alerting a fact-checking organisation."
        else:
            risk_level = "Critical"
            action = "Do not share this content. File a report at cybercrime.gov.in immediately. Preserve the evidence bundle unaltered. Seek legal advice if the content involves your identity."

        # Step 4 — Build report object
        report = InvestigationReport(
            session_id=session_id,
            timestamp=datetime.datetime.utcnow().isoformat(),
            claim_submitted=claim_text,
            visual_manipulation_confidence=visual_results.get("manipulation_confidence", 0),
            visual_anomaly_count=visual_results.get("anomaly_count", 0),
            visual_primary_indicators=visual_results.get("primary_indicators", []),
            visual_summary=visual_results.get("summary", ""),
            metadata_anomalies=visual_results.get("metadata_anomalies", []),
            context_verified_count=context_results.get("verified_count", 0),
            context_contradicted_count=context_results.get("contradicted_count", 0),
            context_unverifiable_count=context_results.get("unverifiable_count", 0),
            context_confidence=context_results.get("context_confidence", 0),
            context_sources=context_results.get("sources", []),
            harm_category=harm_category,
            harm_severity_score=harm_severity_score,
            risk_level=risk_level,
            recommended_action=action,
            evidence_bundle_path="",
            context_sub_claims=context_results.get("sub_claims", [])
        )

        # Step 5 — Generate evidence bundle
        bundle_path = create_evidence_bundle(report, image_path, session_dir)
        report.evidence_bundle_path = bundle_path

        # Step 6 — Audit and return
        write_audit_log(session_id, "triage_complete", {
            "risk_level": risk_level,
            "score": harm_severity_score,
            "category": harm_category
        })

        return report.to_dict()

    except Exception as e:
        # Fallback safe dictionary return
        return {
            "session_id": session_id,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "claim_submitted": claim_text,
            "visual_manipulation_confidence": visual_results.get("manipulation_confidence", 0),
            "visual_anomaly_count": visual_results.get("anomaly_count", 0),
            "visual_primary_indicators": visual_results.get("primary_indicators", []),
            "visual_summary": visual_results.get("summary", ""),
            "metadata_anomalies": visual_results.get("metadata_anomalies", []),
            "context_verified_count": context_results.get("verified_count", 0),
            "context_contradicted_count": context_results.get("contradicted_count", 0),
            "context_unverifiable_count": context_results.get("unverifiable_count", 0),
            "context_confidence": context_results.get("context_confidence", 0),
            "context_sources": context_results.get("sources", []),
            "harm_category": "Entertainment / Low Risk",
            "harm_severity_score": 0,
            "risk_level": "Low",
            "recommended_action": "Triage failed: " + str(e),
            "evidence_bundle_path": "",
            "error": True
        }

def compile_triage_report(
    session_id: str,
    forensics_result: Dict[str, Any],
    context_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compatibility wrapper matching the original compile_triage_report signature.
    """
    try:
        # Construct standard sub-result models to pass to generate_report
        visual = {
            "manipulation_confidence": int(forensics_result.get("confidence_score", 0.0) * 100),
            "anomaly_count": len(forensics_result.get("forgery_indicators", [])),
            "primary_indicators": forensics_result.get("forgery_indicators", []),
            "summary": forensics_result.get("notes", ""),
            "metadata_anomalies": list(forensics_result.get("metadata_summary", {}).values())
        }
        context = {
            "verified_count": len(context_result.get("claims_analyzed", [])) if context_result.get("is_context_valid") else 0,
            "contradicted_count": len(context_result.get("discrepancies", [])),
            "unverifiable_count": 0,
            "context_confidence": int(context_result.get("contextual_score", 0.0) * 100),
            "sources": context_result.get("verification_sources", [])
        }
        
        # Call generate_report with standard/mock values
        res = generate_report(
            visual_results=visual,
            context_results=context,
            claim_text="Compatibility claim",
            image_path="dummy.png",
            session_id=session_id,
            session_dir="C:\\Users\\varad\\.gemini\antigravity-ide\\scratch\\truthguard\\tmp"
        )
        
        return {
            "status": "success",
            "result": {
                "session_id": session_id,
                "overall_trust_score": res.get("context_confidence", 0) / 100.0,
                "visual_forensics": forensics_result,
                "context_verification": context_result,
                "verdict": "VERIFIED" if res.get("risk_level") == "Low" else "SUSPICIOUS" if res.get("risk_level") == "Medium" else "FALSIFIED",
                "summary": res.get("visual_summary", "")
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error_code": "REPORT_COMPILATION_EXCEPTION",
            "message": f"Failed to compile triage report compatibility: {str(e)}"
        }

def export_to_pdf(report_data: Dict[str, Any], output_path: str) -> Dict[str, Any]:
    """
    Generates a PDF version of the triage report using ReportLab.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(output_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 750, "TruthGuard Forensic Triage Report")
        
        c.setFont("Helvetica", 10)
        c.drawString(50, 730, f"Session ID: {report_data.get('session_id', 'N/A')}")
        c.drawString(50, 715, f"Verdict: {report_data.get('verdict', 'N/A')}")
        c.drawString(50, 700, f"Overall Trust Score: {report_data.get('overall_trust_score', 0.0)}")
        
        c.drawString(50, 675, "Summary:")
        text_object = c.beginText(50, 660)
        text_object.setFont("Helvetica", 9)
        summary_text = report_data.get('summary', '')
        for line in [summary_text[i:i+80] for i in range(0, len(summary_text), 80)]:
            text_object.textLine(line)
        c.drawText(text_object)
        
        c.save()
        return {
            "status": "success",
            "pdf_path": output_path
        }
    except Exception as e:
        return {
            "status": "error",
            "error_code": "PDF_EXPORT_EXCEPTION",
            "message": f"Failed to export report to PDF: {str(e)}"
        }
