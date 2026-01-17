import streamlit as st
import pdfplumber
from docx import Document
from docx.shared import Pt
from io import BytesIO
import re

# --- WORKDAY SUCCESS LOGIC ---

def clean_text_for_ats(text):
    """Removes weird characters and normalizes dates for Workday."""
    # Force dates to MM/YYYY format (Workday's favorite)
    # Replaces things like "Jan 2022" or "01-22" with "01/2022"
    date_pattern = r'([A-Za-z]{3,9}|\d{1,2})[\s,./-]{1,2}(\d{2,4})'
    def date_fix(match):
        return f"{match.group(1)}/{match.group(2)}"
    
    text = re.sub(date_pattern, date_fix, text)
    return text

def create_workday_docx(raw_text):
    """Builds a docx from scratch with NO tables, NO columns."""
    doc = Document()
    
    # Set Standard Font (Calibri/Arial are safest for ATS)
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    # ATS Sections Workday looks for
    headers = ["EXPERIENCE", "EDUCATION", "SKILLS", "SUMMARY", "PROJECTS", "CERTIFICATIONS"]

    for line in raw_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Check if line is a Header
        is_header = any(h in line.upper() for h in headers) and len(line) < 30
        
        if is_header:
            para = doc.add_paragraph()
            run = para.add_run(line.upper())
            run.bold = True
            para.paragraph_format.space_before = Pt(12)
        else:
            doc.add_paragraph(line)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- STREAMLIT FRONTEND (THE UI) ---

st.set_page_config(page_title="Workday Resume Fixer", page_icon="✅")

# CSS to make it look professional
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #0078d4; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏹 Workday Auto-fill Fixer")
st.subheader("Stop re-typing your resume. Convert it to ATS-Perfect format.")

# THE UPLOAD BUTTON
uploaded_file = st.file_uploader("Upload your current Resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])

if uploaded_file:
    with st.spinner("Analyzing and Re-structuring for Workday..."):
        # 1. Extraction
        ext = uploaded_file.name.split('.')[-1].lower()
        if ext == "pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                raw_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        elif ext == "docx":
            doc = Document(uploaded_file)
            raw_text = "\n".join([p.text for p in doc.paragraphs])
        else:
            raw_text = uploaded_file.read().decode("utf-8")

        # 2. Workday Optimization
        cleaned_text = clean_text_for_ats(raw_text)
        final_docx = create_workday_docx(cleaned_text)

        st.success("✅ Optimization Complete!")

        # 3. THE DOWNLOAD BUTTON
        st.download_button(
            label="⬇️ Download Workday-Ready Resume (.docx)",
            data=final_docx,
            file_name=f"Workday_Ready_{uploaded_file.name.split('.')[0]}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        st.warning("Note: This file is designed for bots, not humans. Use it for the 'Apply with Resume' button to ensure 100% auto-fill accuracy.")
