import streamlit as st
import pdfplumber
from docx import Document
from docx.shared import Pt
from io import BytesIO
import re
import spacy

# Load NLP model (English)
nlp = spacy.load("en_core_web_sm")

# --- FIELD EXTRACTION LOGIC ---

def extract_contact_info(text):
    """Extracts name, email, phone from resume text using regex + NLP."""
    doc = nlp(text)

    # Name (first PERSON entity found)
    name = None
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text
            break

    # Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    email = email_match.group(0) if email_match else None

    # Phone
    phone_match = re.search(r'(\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}', text)
    phone = phone_match.group(0) if phone_match else None

    return {
        "name": name or "Unknown",
        "email": email or "Unknown",
        "phone": phone or "Unknown"
    }

def clean_text_for_ats(text):
    """Normalize dates and remove weird characters."""
    date_pattern = r'([A-Za-z]{3,9}|\d{1,2})[\s,./-]{1,2}(\d{2,4})'
    def date_fix(match):
        return f"{match.group(1)}/{match.group(2)}"
    return re.sub(date_pattern, date_fix, text)

def create_workday_docx(parsed_data, raw_text):
    """Builds ATS-friendly DOCX with structured sections."""
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

    # Sections
    headers = ["SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS", "PROJECTS", "CERTIFICATIONS"]

    for line in raw_text.split('\n'):
        line = line.strip()
        if not line:
            continue

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

# --- STREAMLIT FRONTEND ---

st.set_page_config(page_title="Workday Resume Fixer", page_icon="✅")
st.title("🏹 Workday Auto-fill Fixer")
st.subheader("Convert your resume into ATS-perfect format.")

uploaded_file = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

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

        # Clean text for ATS
        cleaned_text = clean_text_for_ats(raw_text)

        # Build ATS-ready DOCX
        final_docx = create_workday_docx(parsed_data, cleaned_text)

        st.success("✅ Resume optimized for Workday!")

        st.download_button(
            label="⬇️ Download Workday-Ready Resume (.docx)",
            data=final_docx,
            file_name=f"Workday_Ready_{uploaded_file.name.split('.')[0]}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
