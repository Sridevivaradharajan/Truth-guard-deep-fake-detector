from pydantic import BaseModel, Field
from typing import List, Dict, Any

class VisualForensicsResult(BaseModel):
    """Schema for visual forensics verification results."""
    is_altered: bool = Field(..., description="True if the image shows signs of tampering, splicing, or editing.")
    confidence_score: float = Field(..., description="Confidence score of the assessment from 0.0 to 1.0.")
    forgery_indicators: List[str] = Field(..., description="List of detected anomalies or visual inconsistencies.")
    metadata_summary: Dict[str, Any] = Field(..., description="Extracted metadata and EXIF properties.")
    notes: str = Field(..., description="Detailed forensic notes and visual analysis findings.")

class ContextVerificationResult(BaseModel):
    """Schema for context and claim verification results."""
    is_context_valid: bool = Field(..., description="True if the claims in the image match reality and verified context.")
    claims_analyzed: List[str] = Field(..., description="List of specific claims extracted and evaluated.")
    verification_sources: List[str] = Field(..., description="List of external sources or links checked.")
    discrepancies: List[str] = Field(..., description="List of contradictions or factual discrepancies found.")
    contextual_score: float = Field(..., description="Trust score of context alignment from 0.0 to 1.0.")

class TriageReportResult(BaseModel):
    """Schema for the final consolidated triage report."""
    session_id: str = Field(..., description="Unique ID for the session.")
    overall_trust_score: float = Field(..., description="Consolidated trust score combining visual and context checks (0.0 to 1.0).")
    visual_forensics: VisualForensicsResult = Field(..., description="Forensic analysis result details.")
    context_verification: ContextVerificationResult = Field(..., description="Context verification details.")
    verdict: str = Field(..., description="Final verdict: VERIFIED, SUSPICIOUS, or FALSIFIED.")
    summary: str = Field(..., description="An executive summary summarizing the findings.")

class ErrorResult(BaseModel):
    """Schema for structured error JSON responses."""
    status: str = Field("error", description="Indicates the operation was an error.")
    error_code: str = Field(..., description="Upper-case unique error code string.")
    message: str = Field(..., description="Detailed descriptive message explaining the error.")

# Dataclass for TruthGuard Investigation Report
from dataclasses import dataclass, asdict

@dataclass
class InvestigationReport:
    session_id: str
    timestamp: str
    claim_submitted: str
    visual_manipulation_confidence: int
    visual_anomaly_count: int
    visual_primary_indicators: list
    visual_summary: str
    metadata_anomalies: list
    context_verified_count: int
    context_contradicted_count: int
    context_unverifiable_count: int
    context_confidence: int
    context_sources: list
    harm_category: str
    harm_severity_score: int
    risk_level: str
    recommended_action: str
    evidence_bundle_path: str
    context_sub_claims: list = None

    def to_dict(self) -> dict:
        """Returns all fields as a plain Python dictionary."""
        return asdict(self)

    def to_report_text(self) -> str:
        """Returns a formatted string of the investigation report in a precise layout."""
        total = self.context_verified_count + self.context_contradicted_count + self.context_unverifiable_count
        indicators_str = ", ".join(self.visual_primary_indicators) if self.visual_primary_indicators else "None"
        metadata_str = ", ".join(self.metadata_anomalies) if self.metadata_anomalies else "None detected"
        sources_str = "\n".join(f"  {url}" for url in self.context_sources) if self.context_sources else ""

        return f"""TRUTHGUARD INVESTIGATION REPORT
Session ID     : {self.session_id}
Timestamp      : {self.timestamp}
Claim          : {self.claim_submitted}

VISUAL FORENSICS
Confidence     : {self.visual_manipulation_confidence}%
Anomalies      : {self.visual_anomaly_count} of 7 items flagged
Indicators     : {indicators_str}
Summary        : {self.visual_summary}
Metadata Flags : {metadata_str}

CONTEXT VERIFICATION
Verified       : {self.context_verified_count} of {total} sub-claims
Contradicted   : {self.context_contradicted_count} of {total} sub-claims
Confidence     : {self.context_confidence}%
Sources:
{sources_str}

TRIAGE ASSESSMENT
Harm Category  : {self.harm_category}
Severity Score : {self.harm_severity_score} / 100
Risk Level     : {self.risk_level}

RECOMMENDED ACTION
{self.recommended_action}"""

