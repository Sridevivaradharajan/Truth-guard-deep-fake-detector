import streamlit as st
import os
import uuid
import tempfile
import json
from dotenv import load_dotenv

# Load configuration
load_dotenv()

from app.agents.coordinator import investigate

# PAGE CONFIG (first Streamlit call)
st.set_page_config(page_title="TruthGuard — Forensic Triage Dashboard", page_icon="🛡️", layout="wide")

# Inject Subtle Professional CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

/* Typography & Base Theme */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif;
}

/* Base Theme Dark Slate background */
.stApp {
    background-color: #0f172a;
    color: #f1f5f9;
}

/* High Contrast Label Visibility Fixes */
label, p[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] {
    color: #f8fafc !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.25px !important;
}

/* File Uploader Dropzone Styling */
[data-testid="stFileUploadDropzone"] {
    background-color: #1e293b !important;
    border: 1px dashed #334155 !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploadDropzone"] div, [data-testid="stFileUploadDropzone"] span, [data-testid="stFileUploadDropzone"] p {
    color: #cbd5e1 !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploadDropzone"] button,
[data-testid="stFileUploader"] button,
[data-testid="stFileUploader"] button[data-testid="stBaseButton-secondary"] {
    background-color: #334155 !important;
    color: #f8fafc !important;
    border: 1px solid #475569 !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    transition: background-color 0.2s ease !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploadDropzone"] button:hover,
[data-testid="stFileUploader"] button:hover {
    background-color: #475569 !important;
}
[data-testid="stFileUploader"] [data-testid="stFileUploadDropzone"] button *,
[data-testid="stFileUploader"] button * {
    color: #f8fafc !important;
    -webkit-text-fill-color: #f8fafc !important;
}

/* Input Fields Background, Text Color, and Focus Indicators */
div[data-baseweb="textarea"], div[data-baseweb="textarea"] > div {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    transition: border-color 0.15s ease-in-out !important;
}
div[data-baseweb="textarea"]:focus-within, div[data-baseweb="textarea"] > div:focus-within {
    border-color: #3b82f6 !important;
}
div[data-baseweb="textarea"] textarea {
    color: #f8fafc !important;
    background-color: transparent !important;
    -webkit-text-fill-color: #f8fafc !important;
    caret-color: #f8fafc !important;
}
div[data-baseweb="input"], div[data-baseweb="input"] > div {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    transition: border-color 0.15s ease-in-out !important;
}
div[data-baseweb="input"]:focus-within, div[data-baseweb="input"] > div:focus-within {
    border-color: #3b82f6 !important;
}
div[data-baseweb="input"] input {
    color: #f8fafc !important;
    background-color: transparent !important;
    -webkit-text-fill-color: #f8fafc !important;
    caret-color: #f8fafc !important;
}

/* Title Styling - Clean Solid White */
.main-title {
    color: #f8fafc;
    font-size: 2.6rem;
    font-weight: 700;
    margin-bottom: 2px;
    letter-spacing: -0.5px;
}

/* Professional Card Panels */
.forensic-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}

/* Custom Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background-color: #1e293b !important;
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid #334155 !important;
}
.stTabs [data-baseweb="tab"] {
    height: 45px;
    white-space: pre-wrap;
    background-color: transparent;
    border-radius: 6px;
    color: #94a3b8 !important;
    font-weight: 600;
    font-size: 0.95rem;
    transition: all 0.2s ease;
    border: none !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #f1f5f9 !important;
    background-color: rgba(255, 255, 255, 0.03);
}
.stTabs [aria-selected="true"] {
    background-color: rgba(37, 99, 235, 0.1) !important;
    color: #3b82f6 !important;
    border-bottom: 2px solid #3b82f6 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #3b82f6 !important;
}

/* Subtle Submit Button */
div.stButton > button {
    background-color: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    box-shadow: none !important;
    transition: background-color 0.2s ease !important;
    width: 100%;
}
div.stButton > button:hover {
    background-color: #1d4ed8 !important;
    cursor: pointer;
}
div.stButton > button:disabled {
    background-color: #334155 !important;
    color: #64748b !important;
}

/* Soft Download Button */
div[data-testid="stDownloadButton"] > button {
    background-color: #059669 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-weight: 500 !important;
    transition: background-color 0.2s ease !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    background-color: #047857 !important;
}

/* Subclaim Fact Check Cards */
.subclaim-card {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}
.subclaim-supported {
    border-left: 4px solid #10b981;
}
.subclaim-contradicted {
    border-left: 4px solid #ef4444;
}
.subclaim-unverifiable {
    border-left: 4px solid #f59e0b;
}

/* Custom Pills */
.pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 4px;
}
.pill-supported { background: rgba(16, 185, 129, 0.1); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); }
.pill-contradicted { background: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.2); }
.pill-unverifiable { background: rgba(245, 158, 11, 0.1); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.2); }

/* Interactive Source Link Buttons */
.source-link {
    display: flex;
    align-items: center;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    text-decoration: none;
    color: #cbd5e1 !important;
    transition: all 0.2s ease;
}
.source-link:hover {
    background: #334155;
    border-color: #3b82f6;
}

/* Bullet list override for markdown */
ul {
    padding-left: 1.2rem;
}

/* Streamlit Chat Message container styling overrides */
[data-testid="stChatMessage"] {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    margin-bottom: 12px !important;
    padding: 12px 16px !important;
}
[data-testid="stChatMessage"] p, 
[data-testid="stChatMessage"] span, 
[data-testid="stChatMessage"] div,
[data-testid="stChatMessage"] {
    color: #f8fafc !important;
}

/* Streamlit Chat Input container overrides (Removes white box wrapper) */
[data-testid="stChatInput"] {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}
[data-testid="stChatInput"] > div {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}
[data-testid="stChatInput"] textarea {
    color: #f8fafc !important;
    background-color: transparent !important;
    -webkit-text-fill-color: #f8fafc !important;
    caret-color: #f8fafc !important;
}
</style>
""", unsafe_allow_html=True)

# HEADER SECTION
st.markdown('<div class="main-title">🛡️ TruthGuard</div>', unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1rem; color: #94a3b8; margin-top: -5px; margin-bottom: 25px;'>AI-Powered Misinformation Triage & Digital Forensics System</p>", unsafe_allow_html=True)

# LAYOUT SPLIT
left, right = st.columns([4, 6], gap="large")

# LEFT PANEL — CONTROLS & INPUTS
with left:
    st.markdown('<h3 style="color: #f1f5f9; font-size: 1.3rem; font-weight: 600; margin-bottom: 15px;">🔍 Forensic Control Panel</h3>', unsafe_allow_html=True)
    
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Upload Suspicious Media",
            type=["jpg", "jpeg", "png", "webp"],
            help="Supported formats: JPEG, PNG, WEBP. Max size: 10MB."
        )
        
        # Display image preview immediately upon upload
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Target Media Preview", use_container_width=True)
            
        claim_text = st.text_area(
            "Paired Claim Text",
            placeholder="Type or paste the exact statement/claim paired with this image...",
            max_chars=500,
            height=120
        )
        
        submit = st.button(
            "Run Forensic Investigation",
            disabled=(uploaded_file is None or len(claim_text.strip()) == 0)
        )
    
    if uploaded_file is not None:
        st.markdown(
            """
            <div style="background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.15); border-radius: 12px; padding: 15px; margin-top: 15px;">
                <div style="font-size: 0.85rem; color: #38bdf8; font-weight: 600; margin-bottom: 4px;">💡 Visual Search Tip:</div>
                <div style="font-size: 0.85rem; color: #94a3b8; line-height: 1.4;">
                    To trace the primary source of this image, perform a reverse-image lookup on <a href="https://lens.google.com" target="_blank" style="color: #38bdf8; text-decoration: underline;">Google Lens</a> or <a href="https://tineye.com" target="_blank" style="color: #38bdf8; text-decoration: underline;">TinEye</a>.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# RIGHT PANEL — RESULTS DASHBOARD
with right:
    st.markdown('<h3 style="color: #f1f5f9; font-size: 1.3rem; font-weight: 600; margin-bottom: 15px;">📊 Investigation Dashboard</h3>', unsafe_allow_html=True)
    
    if submit:
        # Validate file size
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("File exceeds 10MB limits. Upload a compressed image.")
            st.stop()

        # Windows-compatible temporary location handling
        temp_dir = tempfile.gettempdir() if os.name == "nt" else "/tmp"
        os.makedirs(temp_dir, exist_ok=True)

        ext = os.path.splitext(uploaded_file.name)[1]
        tmp_path = os.path.join(temp_dir, f"tg_upload_{uuid.uuid4().hex}{ext}")
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.read())

        with st.spinner("Analyzing image features, searching context databases, and computing triage risk..."):
            report = investigate(tmp_path, claim_text)

        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        st.session_state["last_report"] = report

    # RENDER INVESTIGATION RESULTS
    def render_empty_state(tab_name: str):
        st.markdown(
            f"""
            <div class="forensic-card" style="text-align: center; padding: 50px 30px; margin-top: 15px;">
                <div style="font-size: 3rem; margin-bottom: 15px;">🛡️</div>
                <h4 style="color: #f1f5f9; font-weight: 600; font-size: 1.15rem;">Awaiting Investigation</h4>
                <p style="color: #94a3b8; font-size: 0.9rem; line-height: 1.5; max-width: 400px; margin: 0 auto 12px auto;">
                    Please upload an image and enter the associated claim in the left panel, then run the investigation to generate findings for the <b>{tab_name}</b>.
                </p>
                <div style="display: inline-block; padding: 4px 12px; background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.15); border-radius: 20px; font-size: 0.85rem; color: #3b82f6; font-weight: 500;">
                    Ready for analysis
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    has_report = "last_report" in st.session_state
    report = st.session_state["last_report"] if has_report else None

    # 2. Tabs Interface for Structured Details (Always visible!)
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Executive Summary", 
        "🔍 Context Fact-Check", 
        "🔬 Image Forensics", 
        "📦 Export & Bundle",
        "💬 Forensic Chatbot"
    ])

    # TAB 1: EXECUTIVE SUMMARY
    with tab1:
        if not has_report:
            render_empty_state("Executive Summary")
        elif report.get("error"):
            st.error("Forensic investigation could not be completed.")
            with st.expander("Diagnostic Error Details", expanded=True):
                st.write(report.get("message", "Unknown coordination error occurred."))
        else:
            risk_level = report["risk_level"]
            severity_score = report["harm_severity_score"]
            harm_category = report["harm_category"]
            recommended_action = report["recommended_action"]
            
            # Map risk level to color
            risk_colors = {
                "Critical": "#ef4444",
                "High": "#f97316",
                "Medium": "#f59e0b",
                "Low": "#10b981"
            }
            risk_color = risk_colors.get(risk_level, "#f1f5f9")

            # Custom Metric Cards (Custom HTML + CSS)
            st.markdown(f"""
            <div style="display: flex; gap: 16px; margin-bottom: 20px;">
                <div style="flex: 1; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px; text-align: center;">
                    <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Triage Risk Level</div>
                    <div style="font-size: 1.8rem; font-weight: 700; margin-top: 8px; color: {risk_color};">{risk_level}</div>
                </div>
                <div style="flex: 1; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px; text-align: center;">
                    <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Severity Score</div>
                    <div style="font-size: 1.8rem; font-weight: 700; margin-top: 8px; color: #38bdf8;">{severity_score} <span style="font-size: 1rem; font-weight: 400; color: #94a3b8;">/ 100</span></div>
                </div>
                <div style="flex: 1; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px; text-align: center;">
                    <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Harm Category</div>
                    <div style="font-size: 1.15rem; font-weight: 700; margin-top: 14px; color: #a855f7; line-height: 1.2;">{harm_category}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Severity progress bar
            st.progress(severity_score / 100, text=f"Harm Severity Rating: {severity_score}/100")
            st.write("")

            st.markdown(f"""
            <div style="background: rgba(56, 189, 248, 0.06); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 12px; padding: 20px; margin-bottom: 20px;">
                <div style="font-size: 0.85rem; font-weight: 600; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">🛡️ Recommended Mitigation Action</div>
                <div style="font-size: 1rem; color: #e2e8f0; line-height: 1.5; font-weight: 500;">{recommended_action}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<p style="font-size: 1.05rem; font-weight: 600; color: #f1f5f9; margin-bottom: 10px;">Summary Findings</p>', unsafe_allow_html=True)
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 10px; padding: 15px;">
                    <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500; text-transform: uppercase;">Image Manipulation</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #f43f5e; margin: 5px 0;">{report['visual_manipulation_confidence']}%</div>
                    <div style="font-size: 0.85rem; color: #94a3b8;">Confidence score of image tampering/AI generation.</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_right:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 10px; padding: 15px;">
                    <div style="font-size: 0.8rem; color: #94a3b8; font-weight: 500; text-transform: uppercase;">Claim Context Score</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #10b981; margin: 5px 0;">{report['context_confidence']}%</div>
                    <div style="font-size: 0.85rem; color: #94a3b8;">Factual alignment score against web sources.</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.write("")
            st.markdown('<p style="font-size: 0.95rem; font-weight: 600; color: #cbd5e1; margin-bottom: 5px;">Visual Forensics Synopsis</p>', unsafe_allow_html=True)
            st.info(report['visual_summary'] or "No specific anomalies identified.")

    # TAB 2: CONTEXT FACT-CHECK
    with tab2:
        if not has_report:
            render_empty_state("Context Fact-Check")
        elif report.get("error"):
            st.warning("No fact-check details available due to an investigation error.")
        else:
            st.markdown(f"""
            <div style="margin-bottom: 20px;">
                <span style="color:#94a3b8; font-size:0.9rem;">Sub-claims evaluated:</span>
                <strong style="color:#10b981;">{report['context_verified_count']} verified</strong> · 
                <strong style="color:#ef4444;">{report['context_contradicted_count']} contradicted</strong> · 
                <strong style="color:#f59e0b;">{report['context_unverifiable_count']} unverifiable</strong>
            </div>
            """, unsafe_allow_html=True)
            
            if report.get("context_sub_claims"):
                for item in report["context_sub_claims"]:
                    verdict = item.get("verdict", "UNVERIFIABLE")
                    sub_claim = item.get("sub_claim", "")
                    evidence = item.get("evidence", "No details.")
                    confidence = item.get("confidence", 0)
                    
                    card_class = "subclaim-unverifiable"
                    pill_class = "pill-unverifiable"
                    icon = "⚠️"
                    if verdict == "SUPPORTED":
                        card_class = "subclaim-supported"
                        pill_class = "pill-supported"
                        icon = "✅"
                    elif verdict == "CONTRADICTED":
                        card_class = "subclaim-contradicted"
                        pill_class = "pill-contradicted"
                        icon = "❌"
                        
                    st.markdown(f"""
                    <div class="subclaim-card {card_class}">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div style="font-weight: 600; font-size: 0.95rem; color: #f1f5f9; padding-right: 15px;">{icon} {sub_claim}</div>
                            <span class="pill {pill_class}">{verdict}</span>
                        </div>
                        <div style="margin-top: 10px; font-size: 0.9rem; color: #cbd5e1; line-height: 1.45;">
                            <strong>Evidence:</strong> {evidence}
                        </div>
                        <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 8px;">Confidence level: {confidence}%</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Render Supporting Sources Links cleanly
            if report.get("context_sources"):
                st.write("")
                st.markdown('<p style="font-size: 1rem; font-weight: 600; color: #f1f5f9; margin-bottom: 10px;">🌐 Verified Sources Checked</p>', unsafe_allow_html=True)
                for url in report["context_sources"]:
                    # Truncate long URLs for clean display
                    display_url = url[:70] + "..." if len(url) > 70 else url
                    st.markdown(f"""
                    <a href="{url}" target="_blank" class="source-link">
                        <span style="margin-right: 10px;">🔗</span>
                        <span style="font-size: 0.85rem; font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{display_url}</span>
                    </a>
                    """, unsafe_allow_html=True)

    # TAB 3: IMAGE FORENSICS
    with tab3:
        if not has_report:
            render_empty_state("Image Forensics")
        elif report.get("error"):
            st.warning("No image forensics details available due to an investigation error.")
        else:
            st.markdown(f"""
            <div style="margin-bottom: 20px;">
                <span style="color:#94a3b8; font-size:0.9rem;">Checklist items flagged:</span>
                <strong style="color:#f43f5e; font-size: 1.1rem;">{report['visual_anomaly_count']} <span style="font-size:0.9rem; font-weight:400; color:#94a3b8;">out of 7</span></strong>
            </div>
            """, unsafe_allow_html=True)
            
            # Visual Primary Indicators (pills)
            if report.get("visual_primary_indicators"):
                st.markdown('<p style="font-size: 0.9rem; font-weight: 600; color: #cbd5e1; margin-bottom: 5px;">Primary Forensic Anomaly Flags</p>', unsafe_allow_html=True)
                pills_html = ""
                for indicator in report["visual_primary_indicators"]:
                    pills_html += f'<span style="display:inline-block; padding: 4px 10px; margin-right: 8px; margin-bottom: 8px; font-size: 0.8rem; background: rgba(244, 63, 94, 0.15); border: 1px solid rgba(244, 63, 94, 0.3); border-radius: 8px; color: #fb7185; font-weight: 500;">🚨 {indicator.replace("_", " ")}</span>'
                st.markdown(f"<div>{pills_html}</div>", unsafe_allow_html=True)
                st.write("")

            # Metadata anomalies list
            st.markdown('<p style="font-size: 0.9rem; font-weight: 600; color: #cbd5e1; margin-bottom: 5px;">Metadata / EXIF Warnings</p>', unsafe_allow_html=True)
            if report.get("metadata_anomalies"):
                for meta in report["metadata_anomalies"]:
                    st.markdown(f"""
                    <div style="background: rgba(245, 158, 11, 0.08); border: 1px dashed rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; color: #fbbf24; margin-bottom: 8px;">
                        ⚠️ <strong>Warning:</strong> {meta.replace("_", " ").capitalize()} detected.
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; color: #34d399;">
                    ✅ No metadata inconsistencies or EXIF anomalies detected.
                </div>
                """, unsafe_allow_html=True)

            st.write("")
            st.markdown('<p style="font-size: 0.9rem; font-weight: 600; color: #cbd5e1; margin-bottom: 5px;">Analysis Finding Details</p>', unsafe_allow_html=True)
            st.info(report['visual_summary'])

    # TAB 4: EXPORT & BUNDLE
    with tab4:
        if not has_report:
            render_empty_state("Export & Bundle")
        elif report.get("error"):
            st.warning("No export bundle available due to an investigation error.")
        else:
            st.markdown('<p style="font-size: 1rem; font-weight: 600; color: #f1f5f9; margin-bottom: 10px;">📥 Download Evidence Package</p>', unsafe_allow_html=True)
            st.markdown("<p style='font-size: 0.9rem; color: #94a3b8; line-height: 1.5;'>Export a secure, timestamped ZIP package containing the generated report and target media for legal or archival compliance purposes.</p>", unsafe_allow_html=True)
            
            bundle = report.get("evidence_bundle_path", "")
            if bundle and os.path.exists(bundle):
                with open(bundle, "rb") as f:
                    st.download_button(
                        label="📥 Download Evidence Bundle",
                        data=f,
                        file_name="truthguard_evidence.zip",
                        mime="application/zip"
                    )
            else:
                st.warning("Evidence bundle file not found. Re-run investigation to compile.")
            
            st.write("")
            st.markdown('<p style="font-size: 1rem; font-weight: 600; color: #f1f5f9; margin-bottom: 10px;">📋 Raw Investigation Audit Log</p>', unsafe_allow_html=True)
            
            # Reconstruct report text from dict fields
            total = report['context_verified_count'] + report['context_contradicted_count'] + report['context_unverifiable_count']
            indicators_str = ", ".join(report['visual_primary_indicators']) if report['visual_primary_indicators'] else "None"
            metadata_str = ", ".join(report['metadata_anomalies']) if report['metadata_anomalies'] else "None detected"
            sources_str = "\n".join(f"  {url}" for url in report['context_sources']) if report['context_sources'] else ""
            
            txt = f"""TRUTHGUARD INVESTIGATION REPORT
Session ID     : {report['session_id']}
Timestamp      : {report['timestamp']}
Claim          : {report['claim_submitted']}

VISUAL FORENSICS
Confidence     : {report['visual_manipulation_confidence']}%
Anomalies      : {report['visual_anomaly_count']} of 7 items flagged
Indicators     : {indicators_str}
Summary        : {report['visual_summary']}
Metadata Flags : {metadata_str}

CONTEXT VERIFICATION
Verified       : {report['context_verified_count']} of {total} sub-claims
Contradicted   : {report['context_contradicted_count']} of {total} sub-claims
Confidence     : {report['context_confidence']}%
Sources:
{sources_str}

TRIAGE ASSESSMENT
Harm Category  : {report['harm_category']}
Severity Score : {report['harm_severity_score']} / 100
Risk Level     : {report['risk_level']}

RECOMMENDED ACTION
{report['recommended_action']}"""

            st.code(txt, language="text")

    # TAB 5: FORENSIC CHATBOT
    with tab5:
        st.markdown('<p style="font-size: 1rem; font-weight: 600; color: #f1f5f9; margin-bottom: 5px;">💬 Forensic Assistant Chatbot</p>', unsafe_allow_html=True)
        
        session_chat_id = report["session_id"] if has_report else "general"
        chat_key = f"chat_history_{session_chat_id}"
        if chat_key not in st.session_state:
            if has_report:
                st.session_state[chat_key] = [
                    {"role": "assistant", "content": "Hello! I am your TruthGuard forensic assistant. How can I help you understand this investigation?"}
                ]
            else:
                st.session_state[chat_key] = [
                    {"role": "assistant", "content": "Hello! I am your TruthGuard forensic assistant. Since no investigation has been run yet, feel free to ask me general questions about image manipulation detection, EXIF metadata, or fact-checking workflows!"}
                ]

        # Render chat messages
        for msg in st.session_state[chat_key]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Chat input field
        user_question = st.chat_input("Ask a question about the forensics or fact-check...")
        if user_question:
            st.session_state[chat_key].append({"role": "user", "content": user_question})
            with st.chat_message("user"):
                st.write(user_question)

            # Query model
            with st.spinner("Consulting forensic model..."):
                # Format chat context
                formatted_history = ""
                for item in st.session_state[chat_key][:-1]:
                    formatted_history += f"{item['role'].capitalize()}: {item['content']}\n"

                if has_report:
                    total = report['context_verified_count'] + report['context_contradicted_count'] + report['context_unverifiable_count']
                    indicators_str = ", ".join(report['visual_primary_indicators']) if report['visual_primary_indicators'] else "None"
                    metadata_str = ", ".join(report['metadata_anomalies']) if report['metadata_anomalies'] else "None detected"

                    chat_prompt = f"""
You are "TruthGuard Forensic Chatbot", an objective digital forensics analyst.
Your purpose is to answer follow-up questions from the user based strictly on the findings of this investigation.

CLAIM UNDER INVESTIGATION:
"{report['claim_submitted']}"

INVESTIGATION REPORT DETAILS:
- Session ID: {report['session_id']}
- Risk Level: {report['risk_level']}
- Severity Score: {report['harm_severity_score']}/100
- Harm Category: {report['harm_category']}
- Recommended Action: {report['recommended_action']}

VISUAL FORENSICS DETECTED:
- Manipulation Confidence: {report['visual_manipulation_confidence']}%
- Checklist Items Flagged: {report['visual_anomaly_count']} of 7 items
- Anomaly Indicators: {indicators_str}
- Metadata/EXIF Flags: {metadata_str}
- Synopsis: {report['visual_summary']}

CONTEXT FACT-CHECK VERIFICATION:
- Fact-check Alignment Score: {report['context_confidence']}%
- Verified Sub-claims: {report['context_verified_count']} of {total}
- Contradicted Sub-claims: {report['context_contradicted_count']} of {total}
- Unverifiable Sub-claims: {report['context_unverifiable_count']} of {total}
- Decomposed Sub-claims Details:
{json.dumps(report.get('context_sub_claims', []), indent=2)}
- Sources Checked:
{json.dumps(report.get('context_sources', []), indent=2)}

CHAT HISTORY:
{formatted_history}

User's Question: {user_question}

INSTRUCTIONS:
1. Answer the question precisely and objectively based on the findings.
2. If the user asks where a fact or detail is verified, cite the specific sub-claims or URLs from the "Sources Checked".
3. Keep your answers concise, forensic, and direct. Do not speculate beyond what is verified or contradicted in the report.
"""
                else:
                    chat_prompt = f"""
You are "TruthGuard Forensic Chatbot", an objective digital forensics analyst.
No active investigation report has been run yet by the user.

Your purpose is to answer general questions from the user about:
1. Digital image forensics (how to spot AI-generated images, manipulation traces like splicing, hand geometry anomalies, double JPEG compression, EXIF metadata).
2. Fact-checking methodologies (how to verify claims, decompose claims, cross-reference search engine results, assess source trustworthiness).
3. Best practices for media triage and misinformation detection.

CHAT HISTORY:
{formatted_history}

User's Question: {user_question}

INSTRUCTIONS:
1. Answer the user's question professionally, clearly, and concisely.
2. Give actionable tips on how they can use TruthGuard once they run an investigation.
"""
                from app.utils.gemini_client import call_text_model
                response_res = call_text_model(chat_prompt)
                
                if response_res.get("success") is True:
                    assistant_response = response_res["text"].strip()
                else:
                    assistant_response = f"I encountered an error querying the model: {response_res.get('error', 'Unknown Error')}"

            # Save assistant message
            st.session_state[chat_key].append({"role": "assistant", "content": assistant_response})
            st.rerun()
