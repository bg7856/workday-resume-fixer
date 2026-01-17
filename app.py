import streamlit as st
import pdfplumber
from docx import Document
from io import BytesIO

# --- CORE FUNCTIONS ---

def extract_text(uploaded_file):
    """Extracts text based on file type."""
    file_type = uploaded_file.name.split('.')[-1].lower()
    text = ""
    
    if file_type == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    elif file_type == "docx":
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
    else:  # Assume .txt
        text = uploaded_file.read().decode("utf-8")
    
    return text

def create_workday_docx(raw_text):
    """Formats text into a clean Workday-friendly .docx file."""
    doc = Document()
    # Cleaning up the text to be single-column and standard
    for line in raw_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Bold common headers to help the Workday parser
        headers = ["EXPERIENCE", "EDUCATION", "SKILLS", "SUMMARY", "PROJECTS", "CONTACT"]
        if any(h in line.upper() for h in headers) and len(line) < 30:
            para = doc.add_paragraph()
            run = para.add_run(line.upper())
            run.bold = True
        else:
            doc.add_paragraph(line)
            
    # Save to a memory buffer instead of disk (No storage = No compliance risk)
    target_file = BytesIO()
    doc.save(target_file)
    target_file.seek(0)
    return target_file

# --- WEBSITE UI (Streamlit) ---

st.set_page_config(page_title="Workday Resume Fixer", page_icon="📝")
st.title("🚀 $1 Workday Resume Fixer")
st.write("Upload your fancy resume. Get a 'Boring' one that Workday Auto-fills perfectly.")

uploaded_file = st.file_uploader("Upload Resume (PDF, DOCX, or TXT)", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    with st.spinner("Processing..."):
        # 1. Extract
        resume_text = extract_text(uploaded_file)
        
        # 2. Convert
        processed_docx = create_workday_docx(resume_text)
        
        st.success("Conversion Successful!")
        
        # 3. Download Button
        st.download_button(
            label="⬇️ Download Workday-Optimized Resume",
            data=processed_docx,
            file_name=f"workday_fixed_{uploaded_file.name.split('.')[0]}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

st.divider()
st.info("Tip: Workday loves .docx files more than PDFs for auto-filling.")
