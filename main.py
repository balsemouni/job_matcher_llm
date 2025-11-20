import fitz  # PyMuPDF
import os
import re
import json
from pydantic import BaseModel, Field
import google.generativeai as genai
import streamlit as st

# ===================== GEMINI API SETUP =====================
API_KEY = "5555555555555555555555555"  # Replace with your API key
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

# ===================== DATA MODEL =====================
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

# ===================== PDF TEXT EXTRACTION =====================
def extract_text_from_pdf(pdf_path: str) -> str:
    with fitz.open(pdf_path) as doc:
        text = "\n".join(page.get_text("text") for page in doc)
    return text

def normalize_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

# ===================== CV INFO EXTRACTION =====================
def extract_cv_info(text: str) -> ExtractedInfo:
    info = ExtractedInfo()

    section_keywords = {
        "profile": ["Profile", "Summary", "About Me", "Objective", "Professional Summary", "Profil"],
        "technical_skills": ["Technical Skills", "Skills", "Core Competencies", "Technical Expertise", "Compétences", "Compétences Techniques", "Compétences Automobile"],
        "soft_skills": ["Soft Skills", "Interpersonal Skills", "Communication Skills", "Compétences Douces", "Compétences Interpersonnelles"],
        "education": ["Education", "Academic Background", "Degrees", "Studies", "Formation", "Diplômes"],
        "experience": ["Experience", "Work Experience", "Career History", "Employment", "Professional Experience", "Expérience Professionnelle", "Historique Professionnel"],
        "languages": ["Languages", "Language Proficiency", "Spoken Languages", "Langues", "Langue"],
        "certifications": ["Certifications", "Certificates", "Courses & Training", "Certifications", "Cours"],
        "projects": ["Projects", "Academic Projects", "Portfolio", "Achievements", "Projets", "Réalisations"],
    }

    # Extract contact info
    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    phones = re.findall(r"(\+?\d[\d\s().-]{8,}\d)", text)
    info.contact_info = f"Email: {emails[0] if emails else 'Not found'}, Phone: {phones[0] if phones else 'Not found'}"

    # Prepare regex for section headers
    all_section_titles = [re.escape(k) for names in section_keywords.values() for k in names]
    combined_pattern = r"(?im)^\s*(" + "|".join(all_section_titles) + r")\b"

    matches = [(m.start(), m.group().strip()) for m in re.finditer(combined_pattern, text)]
    matches.append((len(text), "END"))

    # Extract content for each section
    for i in range(len(matches) - 1):
        start_pos, section_title = matches[i]
        end_pos, _ = matches[i + 1]
        content = text[start_pos:end_pos].strip()

        for field, names in section_keywords.items():
            if any(section_title.lower().startswith(n.lower()) for n in names):
                clean = re.sub(rf"(?i)^{re.escape(section_title)}\s*[:\-]*", "", content).strip()
                clean = re.sub(r"\s+", " ", clean)
                clean = clean[:1000] + "..." if len(clean) > 1000 else clean
                setattr(info, field, clean)
                break

    return info

# ===================== JOB MATCHING =====================
def analyze_cv_for_job(cv_text: str, job_description: str):
    prompt = f"""
You are an **unfiltered senior HR evaluator**. Your tone must be strict, direct, and brutally honest.
NO sugarcoating, NO politeness, NO compliments.

Your job:
1. Evaluate the candidate’s CV against the job description.
2. Score harshly (0–100) based ONLY on factual skill match.
3. Identify missing skills precisely.
4. Suggest practical improvements.
5. Produce a short professional summary (max 3 lines).

Rules:
- Do NOT invent skills.
- Do NOT fill missing info—say "not provided".
- Do NOT output explanations.
- Do NOT add text before or after the JSON.
- Return **VALID JSON ONLY**.

Return EXACTLY this JSON:

{{
  "score": 0-100,
  "missing_skills": ["skill1", "skill2"],
  "improvements": ["tip1", "tip2"],
  "profile_summary": "3-line summary"
}}

CV:
{cv_text}

JOB DESCRIPTION:
{job_description}
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        return json.loads(text)
    except:
        return {
            "score": 0,
            "missing_skills": [],
            "improvements": ["AI failed to generate valid JSON"],
            "profile_summary": "N/A"
        }

# ===================== COMPANY PREDICTION =====================
def llm_predict_companies(extracted_info: ExtractedInfo):
    prompt = f"""
Suggest 10 companies that could hire this candidate.
Return JSON array ONLY.

Candidate Info:
{json.dumps(extracted_info.model_dump(), indent=2)}
"""
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3]
        return json.loads(text)[:10]
    except:
        return [{"company_name": "Error", "reason": "Parsing Failed"}]

# ===================== STREAMLIT UI =====================
def run_streamlit():
    st.set_page_config(page_title="AI CV Analyzer", layout="wide")
    st.title("📄 AI CV Analyzer + Job Matching")

    uploaded_file = st.file_uploader("Upload CV (PDF)", type="pdf")
    if uploaded_file:
        pdf_path = f"temp_{uploaded_file.name}"
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        text = normalize_text(extract_text_from_pdf(pdf_path))
        extracted = extract_cv_info(text)

        col1, col2 = st.columns([1, 1])

        # LEFT: extracted CV info
        with col1:
            st.subheader("Extracted CV Information")
            for key, val in extracted.model_dump().items():
                st.write(f"### {key.replace('_', ' ').title()}")
                st.info(val)
                st.markdown("---")

        # RIGHT: job matching
        with col2:
            st.subheader("🎯 Job Match Analysis")
            job = st.text_area("Paste Job Description")

            if st.button("Analyze Job Fit"):
                with st.spinner("Analyzing..."):
                    result = analyze_cv_for_job(text, job)
                st.success(f"Score: {result['score']} / 100")
                st.write("### Missing Skills")
                for skill in result["missing_skills"]:
                    st.error(f"- {skill}")
                st.write("### Improvements")
                for imp in result["improvements"]:
                    st.warning(f"- {imp}")
                st.write("### Profile Summary")
                st.info(result["profile_summary"])

            st.subheader("🏢 Company Suggestions")
            if st.button("Find Companies"):
                with st.spinner("Generating suggestions..."):
                    companies = llm_predict_companies(extracted)
                for c in companies:
                    st.write(f"### {c.get('company_name', 'N/A')}")
                    st.write(c)
                    st.markdown("---")

        os.remove(pdf_path)

# ===================== MAIN =====================
if __name__ == "__main__":
    run_streamlit()
