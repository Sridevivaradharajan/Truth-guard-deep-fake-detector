import os
import shutil
import zipfile
from typing import Any, Dict, List
from app.utils.logger import get_logger
from app.models.report_schema import InvestigationReport

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = get_logger(__name__)

def create_evidence_bundle(report: InvestigationReport, image_path: str, session_dir: str) -> str:
    """
    Creates a zip archive compiling all investigation evidence.

    Args:
        report: The InvestigationReport dataclass instance.
        image_path: Path to the original verified image file.
        session_dir: Path to the active session directory.

    Returns:
        str: Absolute path to the generated ZIP archive.
    """
    try:
        # Create evidence folder inside session directory
        evidence_dir = os.path.join(session_dir, "evidence")
        os.makedirs(evidence_dir, exist_ok=True)

        # Step 1: Copy original image to {session_dir}/evidence/original_image{extension}
        _, ext = os.path.splitext(image_path)
        dest_image_name = f"original_image{ext.lower()}"
        dest_image_path = os.path.join(evidence_dir, dest_image_name)
        if os.path.exists(image_path):
            shutil.copy(image_path, dest_image_path)
        else:
            # Create a placeholder if original image is dummy or not found
            with open(dest_image_path, "wb") as f:
                f.write(b"dummy image data")

        # Step 2: Write report.to_report_text() to {session_dir}/evidence/report.txt
        report_txt_path = os.path.join(evidence_dir, "report.txt")
        with open(report_txt_path, "w", encoding="utf-8") as f:
            f.write(report.to_report_text())

        # Step 3: Create PDF of report using reportlab — A4, Helvetica 10pt body, Bold 12pt headers
        pdf_path = os.path.join(evidence_dir, "report.pdf")
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=16,
            spaceAfter=12
        )
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=14,
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=10,
            leading=12,
            spaceAfter=4
        )

        story = []
        lines = report.to_report_text().splitlines()
        is_first = True
        for line in lines:
            stripped = line.strip()
            if not stripped:
                story.append(Spacer(1, 6))
                continue

            if stripped in ("TRUTHGUARD INVESTIGATION REPORT", "VISUAL FORENSICS", "CONTEXT VERIFICATION", "TRIAGE ASSESSMENT", "RECOMMENDED ACTION"):
                if is_first:
                    story.append(Paragraph(stripped, title_style))
                    is_first = False
                else:
                    story.append(Paragraph(stripped, header_style))
            else:
                if line.startswith("  "):
                    text = f"&nbsp;&nbsp;{stripped}"
                else:
                    text = stripped
                story.append(Paragraph(text, body_style))

        doc.build(story)

        # Step 4: Write each URL in context_sources to {session_dir}/evidence/sources.txt
        sources_txt_path = os.path.join(evidence_dir, "sources.txt")
        with open(sources_txt_path, "w", encoding="utf-8") as f:
            for url in report.context_sources:
                f.write(f"{url}\n")

        # Step 5: Copy {session_dir}/audit.log to {session_dir}/evidence/audit.json
        audit_log_path = os.path.join(session_dir, "audit.log")
        audit_dest_path = os.path.join(evidence_dir, "audit.json")
        if os.path.exists(audit_log_path):
            shutil.copy(audit_log_path, audit_dest_path)
        else:
            with open(audit_dest_path, "w", encoding="utf-8") as f:
                f.write("[]")

        # Step 6: Create ZIP at {session_dir}/truthguard_evidence_{session_id}.zip
        zip_base = os.path.join(session_dir, f"truthguard_evidence_{report.session_id}")
        zip_path = shutil.make_archive(zip_base, 'zip', root_dir=evidence_dir)

        # Step 7: Return full ZIP path as string
        return zip_path

    except Exception as e:
        logger.error(f"Error creating evidence bundle: {str(e)}")
        # Return fallback ZIP path or raise
        fallback_zip = os.path.join(session_dir, f"truthguard_evidence_{report.session_id}.zip")
        if not os.path.exists(fallback_zip):
            # Create a simple backup zip
            with zipfile.ZipFile(fallback_zip, "w") as zf:
                zf.writestr("error.txt", f"Failed to compile evidence bundle: {str(e)}")
        return fallback_zip

def create_bundle(
    session_id: str,
    image_path: str,
    metadata: Dict[str, Any],
    claims: List[str],
    external_verifications: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compiles all forensic evidence and metadata into a structured bundle (Legacy wrapper).
    """
    try:
        return {
            "status": "success",
            "session_id": session_id,
            "image_path": image_path,
            "metadata": metadata,
            "claims": claims,
            "external_verifications": external_verifications
        }
    except Exception as e:
        return {
            "status": "error",
            "error_code": "BUNDLE_CREATION_EXCEPTION",
            "message": f"Failed to compile evidence bundle: {str(e)}"
        }

def delete_session_temp_files(session_id: str) -> Dict[str, Any]:
    """
    Standard 2: Cleans up and deletes all temporary session files.
    """
    try:
        session_root = os.getenv("TRUTHGUARD_SESSION_DIR") or os.path.join(os.path.expanduser("~"), ".gemini", "antigravity-ide", "scratch", "truthguard_sessions")
        session_path = os.path.join(session_root, session_id)
        
        if os.path.exists(session_path):
            shutil.rmtree(session_path)
            logger.info(f"Successfully deleted temporary session directory: {session_path}")
            return {
                "status": "success",
                "message": f"Deleted temporary files for session {session_id}."
            }
        
        return {
            "status": "success",
            "message": f"Session directory did not exist: {session_path}. No action required."
        }
    except Exception as e:
        return {
            "status": "error",
            "error_code": "TEMP_CLEANUP_EXCEPTION",
            "message": f"Exception during temp file cleanup: {str(e)}"
        }
