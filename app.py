import streamlit as st
import pdfplumber
from docx import Document
from docx.shared import Pt
from io import BytesIO
import re
import os
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"


# --- CONTACT INFO EXTRACTION (Regex + Heuristics) ---

def extract_contact_info(text):
    # Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    email = email_match.group(0) if email_match else "Unknown"

    # Phone
    phone_match = re.search(r'(\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}', text)
    phone = phone_match.group(0) if phone_match else "Unknown"

    # Name (first non-empty line heuristic)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    name = lines[0] if lines else "Unknown"

    return {"name": name, "email": email, "phone": phone}

# --- CLEANING FOR ATS ---

def clean_text_for_ats(text):
    """Normalize dates and remove weird characters."""
    date_pattern = r'([A-Za-z]{3,9}|\d{1,2})[\s,./-]{1,2}(\d{2,4})'
    def date_fix(match):
        return f"{match.group(1)}/{match.group(2)}"
    return re.sub(date_pattern, date_fix, text)

# --- DOCX GENERATOR ---

def create_ats_docx(parsed_data, raw_text, ats_type="workday"):
    doc = Document()

    # Font
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    # Header: Name + Contact
    header = doc.add_paragraph()
    run = header.add_run(f"{parsed_data['name']}\n{parsed_data['email']} | {parsed_data['phone']}")
    run.bold = True
    header.paragraph_format.space_after = Pt(12)

    # ATS Sections
    if ats_type == "workday":
        headers = ["SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS", "PROJECTS", "CERTIFICATIONS"]
    elif ats_type == "lever":
        headers = ["SUMMARY", "WORK EXPERIENCE", "EDUCATION", "KEY SKILLS", "PROJECTS"]
    elif ats_type == "ashby":
        headers = ["SUMMARY", "BACKGROUND", "EDUCATION", "SKILLS", "PROJECTS"]
    else:
        headers = ["SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS"]

    for line in raw_text.split('\n'):
        line = line.strip()
        if not line:
            continue

        is_header = any(h in line.upper() for h in headers) and len(line) < 40
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

# --- STREAMLIT UI ---

st.set_page_config(page_title="ATS Resume Fixer", page_icon="📄", layout="centered")

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #f9fafc; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #0078d4;
        color: white;
        font-weight: bold;
    }
    .stDownloadButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #28a745;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📄 ATS Resume Fixer")
st.subheader("Convert your resume into ATS-perfect format for Workday, Lever, AshbyHQ.")

uploaded_file = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

ats_choice = st.selectbox("Choose ATS Format", ["Workday", "Lever", "AshbyHQ"])

if uploaded_file:
    with st.spinner("Analyzing resume..."):
        ext = uploaded_file.name.split('.')[-1].lower()
        if ext == "pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                raw_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        elif ext == "docx":
            doc = Document(uploaded_file)
            raw_text = "\n".join([p.text for p in doc.paragraphs])
        else:
            raw_text = uploaded_file.read().decode("utf-8")

        # Extract structured fields
        parsed_data = extract_contact_info(raw_text)

        # Clean text
        cleaned_text = clean_text_for_ats(raw_text)

        # Build ATS-ready DOCX
        final_docx = create_ats_docx(parsed_data, cleaned_text, ats_choice.lower())

        st.success(f"✅ Resume optimized for {ats_choice}!")

        st.download_button(
            label=f"⬇️ Download {ats_choice}-Ready Resume (.docx)",
            data=final_docx,
            file_name=f"{ats_choice}_Ready_{uploaded_file.name.split('.')[0]}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        st.info("⚡ Tip: Use this file for 'Apply with Resume' to ensure ATS auto-fill accuracy.")
