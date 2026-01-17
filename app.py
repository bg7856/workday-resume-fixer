import streamlit as st
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO
import re

# 1. WORKDAY RULES ENGINE
def apply_workday_styles(doc):
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

def add_workday_header(doc, text):
    # Workday looks for specific strings in ALL CAPS or Bold
    # Standard headers: EXPERIENCE, EDUCATION, SKILLS
    para = doc.add_paragraph()
    run = para.add_run(text.upper())
    run.bold = True
    para.paragraph_format.space_before = Pt(12)
    para.paragraph_format.space_after = Pt(6)

# 2. THE DATA SURGERY (Regex for Dates & Sections)
def clean_and_reconstruct(raw_text):
    doc = Document()
    apply_workday_styles(doc)
    
    # Workday Success Patterns
    headers = {
        "EXPERIENCE": ["experience", "employment", "work history"],
        "EDUCATION": ["education", "academic"],
        "SKILLS": ["skills", "competencies", "technologies"]
    }

    for line in raw_text.split('\n'):
        clean_line = line.strip()
        if not clean_line: continue

        # Header Detection Logic
        is_header = False
        for category, keywords in headers.items():
            if any(k in clean_line.lower() for k in keywords) and len(clean_line) < 30:
                add_workday_header(doc, category)
                is_header = True
                break
        
        if not is_header:
            # Date Normalization (Force MM/YYYY format)
            # This is the "Magic" that makes Workday Auto-fill work
            date_match = re.search(r'(\d{1,2})[/.-](\d{2,4})', clean_line)
            if date_match:
                # Re-format dates to Workday's favorite: 01/2024
                month = date_match.group(1).zfill(2)
                year = date_match.group(2)
                if len(year) == 2: year = "20" + year
                clean_line = clean_line.replace(date_match.group(0), f"{month}/{year}")
            
            p = doc.add_paragraph(clean_line)
            p.paragraph_format.line_spacing = 1.0

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- FRONTEND REMAINS THE SAME ---
