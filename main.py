import fitz  # PyMuPDF
import os
import re
import json
from pydantic import BaseModel, Field
import google.generativeai as genai
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import streamlit as st


#  CONFIGURE GEMINI API
API_KEY = "API_KEY"  # Replace with your Gemini API key
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")
console = Console()

#  DATA MODEL
class ExtractedInfo(BaseModel):
    profile: str = Field(default="Not specified")
    technical_skills: str = Field(default="Not specified")
    soft_skills: str = Field(default="Not specified")
    education: str = Field(default="Not specified")
    experience: str = Field(default="Not specified")
    languages: str = Field(default="Not specified")
    certifications: str = Field(default="Not specified")
    projects: str = Field(default="Not specified")
    contact_info: str = Field(default="Not specified")

#  TEXT EXTRACTION

def extract_text_from_pdf(pdf_path: str) -> str:
    with fitz.open(pdf_path) as doc:
        text = "\n".join(page.get_text("text") for page in doc)
    return text

def normalize_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

#  LOGICAL CV INFORMATION EXTRACTION
def extract_cv_info(text: str) -> ExtractedInfo:
    info = ExtractedInfo()

    section_keywords = {
        "profile": ["Profile", "Summary", "About Me", "Objective", "Professional Summary"],
        "technical_skills": ["Technical Skills", "Skills", "Core Competencies", "Technical Expertise"],
        "soft_skills": ["Soft Skills", "Interpersonal Skills", "Communication Skills"],
        "education": ["Education", "Academic Background", "Degrees", "Studies"],
        "experience": ["Experience", "Work Experience", "Career History", "Employment", "Professional Experience"],
        "languages": ["Languages", "Language Proficiency", "Spoken Languages"],
        "certifications": ["Certifications", "Certificates", "Courses & Training"],
        "projects": ["Projects", "Academic Projects", "Portfolio", "Achievements"],
    }

    # Contact info detection
    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    phones = re.findall(r"(\+?\d[\d\s().-]{8,}\d)", text)
    info.contact_info = f"Email: {emails[0] if emails else 'Not found'}, Phone: {phones[0] if phones else 'Not found'}"

    # Regex for section headers
    all_section_titles = [re.escape(k) for names in section_keywords.values() for k in names]
    combined_pattern = r"(?i)^(" + "|".join(all_section_titles) + r")\b"
    matches = [(m.start(), m.group().strip()) for m in re.finditer(combined_pattern, text, flags=re.MULTILINE)]
    matches.append((len(text), "END"))

    for i in range(len(matches) - 1):
        start_pos, section_title = matches[i]
        end_pos, _ = matches[i + 1]
        content = text[start_pos:end_pos].strip()
        for field, names in section_keywords.items():
            if any(section_title.lower().startswith(n.lower()) for n in names):
                clean = re.sub(rf"(?i)^{section_title}\s*[:\-]*", "", content).strip()
                clean = re.sub(r"\s+", " ", clean)
                if len(clean) > 1000:
                    clean = clean[:1000] + "..."
                setattr(info, field, clean)
                break

    return info

# COMPANY PREDICTION USING GEMINI (10 COMPANIES)
def llm_predict_companies(extracted_info: ExtractedInfo):
    prompt = f"""
    You are an expert HR AI system.
    Based on this candidate's extracted information, suggest 10 real global companies
    that might hire them. Include the following fields for each company:
      - company_name: string
      - industry: string
      - reason: string (why this candidate fits)
      - email: string (general HR or contact email if publicly available, otherwise "N/A")
      - website: string (company website URL if available, otherwise "N/A")
      - location: string (headquarters or main office, if available, otherwise "N/A")

    Return JSON ONLY in this exact format:
    [
      {{
        "company_name": "string",
        "industry": "string",
        "reason": "string",
        "email": "string",
        "website": "string",
        "location": "string"
      }}
    ]

    Candidate Info:
    {json.dumps(extracted_info.model_dump(), indent=2)}
    """
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()

        companies = json.loads(response_text)
        return companies[:10]
    except Exception as e:
        console.print(f"[red]Error parsing Gemini response: {e}[/red]")
        return [{"company_name": "Error", "industry": "Error", "reason": "Failed to parse response",
                 "email": "N/A", "website": "N/A", "location": "N/A"}]

#  CLI INTERFACE
def read_pdf(source_pdf_path: str):
    console.print(f"[bold cyan]📄 Reading CV: {source_pdf_path}[/bold cyan]\n")
    if not os.path.exists(source_pdf_path):
        console.print(f"[red]⚠️ File not found: {source_pdf_path}[/red]")
        return

    text = extract_text_from_pdf(source_pdf_path)
    normalized = normalize_text(text)
    console.print(Panel.fit(normalized[:600] + "...", title="📝 Normalized Text Sample"))

    extracted = extract_cv_info(normalized)

    table = Table(title="🧠 Extracted CV Information", show_lines=True)
    table.add_column("Field", style="bold green")
    table.add_column("Value", style="white")

    for key, val in extracted.model_dump().items():
        display_val = val[:200] + "..." if len(val) > 200 else val
        table.add_row(key.replace("_", " ").title(), display_val)
    console.print(table)

    console.print("\n🤖 [bold yellow]Predicting suitable companies...[/bold yellow]\n")
    result = llm_predict_companies(extracted)
    console.print(Panel.fit(json.dumps(result, indent=2, ensure_ascii=False), title="🏢 Suggested Companies"))

#  STREAMLIT INTERFACE
def run_streamlit():
    st.set_page_config(page_title="AI CV Analyzer", layout="wide")
    st.title("📄 AI CV Analyzer & Company Matcher")
    st.markdown("Upload your CV to extract information and get company recommendations")

    uploaded_file = st.file_uploader("Upload your CV (PDF)", type="pdf")

    if uploaded_file:
        with st.spinner("Processing your CV..."):
            pdf_path = f"temp_{uploaded_file.name}"
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            text = extract_text_from_pdf(pdf_path)
            text = normalize_text(text)
            extracted = extract_cv_info(text)

            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("📋 Extracted CV Information")
                for key, val in extracted.model_dump().items():
                    st.markdown(f"**{key.replace('_', ' ').title()}**")
                    if val == "Not specified":
                        st.warning("Not found in CV")
                    else:
                        st.info(val)
                    st.markdown("---")

            with col2:
                st.subheader("🏢 Company Recommendations")
                if st.button("🔍 Find Suitable Companies"):
                    with st.spinner("Analyzing your profile..."):
                        companies = llm_predict_companies(extracted)
                        for company in companies:
                            st.markdown(f"""
                            <div style='padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin: 10px 0; background-color: #f9f9f9;'>
                                <h3>🏛️ {company['company_name']}</h3>
                                <p><strong>Industry:</strong> {company['industry']}</p>
                                <p><strong>Why it's a good fit:</strong> {company['reason']}</p>
                                <p><strong>Email:</strong> {company.get('email', 'N/A')}</p>
                                <p><strong>Website:</strong> {company.get('website', 'N/A')}</p>
                                <p><strong>Location:</strong> {company.get('location', 'N/A')}</p>
                            </div>
                            """, unsafe_allow_html=True)

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

# MAIN EXECUTION
if __name__ == "__main__":
    MODE = "STREAMLIT"  # "CLI" or "STREAMLIT"
    if MODE == "CLI":
        read_pdf("balsem.pdf")
    else:
        run_streamlit()
