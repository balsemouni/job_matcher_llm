import re
import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ExtractedInfo

def normalize_text(text: str) -> str:
    """
    Normalize text by removing extra spaces and empty lines
    """
    # Removing extra spaces
    text = re.sub(r"[ \t]+", " ", text)
    # Removing extra empty lines
    text = re.sub(r"\n{2,}", "\n", text)
    # Clean each line
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def extract_cv_info(text: str) -> ExtractedInfo:
    """
    Extract structured information from CV text
    """
    # Create empty ExtractedInfo object
    info = ExtractedInfo()
    
    # Define known section titles
    section_keywords = {
        "profile": ["Profile", "Summary", "About Me", "Objective", "Professional Summary"],
        "technical_skills": ["Technical Skills", "Skills", "Core Competencies", "Technical Competencies"],
        "soft_skills": ["Soft Skills", "Interpersonal Skills", "Personal Skills"],
        "education": ["Education", "Academic Background", "Academic Qualifications"],
        "experience": ["Experience", "Work Experience", "Professional Experience", "Employment History"],
        "languages": ["Languages", "Langues", "Language Skills"],
        "certifications": ["Certifications", "Certificates", "Licenses"],
        "projects": ["Projects", "Portfolio", "Personal Projects"],
    }

    # Extract contact information
    emails = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)
    phones = re.findall(r"(\+?\d[\d\s().-]{8,}\d)", text)
    
    # Save contact info
    info.contact_info = f"Email: {emails[0] if emails else 'Not found'}, Phone: {phones[0] if phones else 'Not found'}"

    # Extract sections
    # Create list of all possible titles
    all_titles = [re.escape(k) for names in section_keywords.values() for k in names]
    
    # Pattern to find section headers (case insensitive, multiline)
    pattern = r"(?im)^\s*(" + "|".join(all_titles) + r")\b"
    # This returns a list of: position in text title found
    matches = [(m.start(), m.group().strip()) for m in re.finditer(pattern, text)]
    # Ensures the last section ends at the end of text.
    matches.append((len(text), "END"))

    for i in range(len(matches) - 1):
        # This takes everything from: The current title line to The next title line
        start, title = matches[i]
        end, _ = matches[i + 1]
        content = text[start:end].strip()
        # Match title to its category
        for field, names in section_keywords.items():
            # Check if this title belongs to this category
            if any(title.lower().startswith(n.lower()) for n in names):
                # Remove the section header from text
                clean = re.sub(rf"(?i){re.escape(title)}\s*[:\-]*", "", content).strip()
                # Store clean section into the object
                setattr(info, field, clean)
                break

    return info