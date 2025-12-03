import json, re
from rag.vector_db import retrieve_relevant_context
from rag.memory import retrieve_memory
from llm.gemini_client import call_gemini_for_json

def analyze_cv_for_job(cv_text, job_desc):
    rag_context = retrieve_relevant_context(job_desc)
    memory_context = retrieve_memory(job_desc)

    print(f"RAG context length: {len(rag_context)}")  # Debug
    print(f"Memory context length: {len(memory_context)}")  # Debug

    prompt = f"""
You are a strict, professional HR evaluator. Be brutally honest. 
Assess the CV against the job description and do not sugarcoat. 
Provide a professional assessment of how suitable the candidate is for this position.

RAG CONTEXT:
{rag_context}

MEMORY:
{memory_context}

CV:
{cv_text}

JOB DESCRIPTION:
{job_desc}

Return valid JSON only with these fields:
{{
  "score": 0,                 # Candidate suitability score 0-100
  "missing_skills": [],       # List of missing or weak skills
  "improvements": [],         # Concrete professional suggestions
  "profile_summary": ""       # Professional summary of the candidate
}}
"""

    try:
        print("Calling Gemini...")  # Debug
        raw = call_gemini_for_json(prompt)
        print(f"Raw response: {raw}")  # Debug
        
        if not raw:
            print("LLM returned no response")  # Debug
            return {
                "score": 0,
                "missing_skills": [],
                "improvements": ["LLM failed - no response"],
                "profile_summary": ""
            }

        # Try direct JSON parsing first
        try:
            result = json.loads(raw)
            print("JSON parsed successfully")  # Debug
            return result
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")  # Debug
            # Fallback: extract JSON from text
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
            else:
                return {
                    "score": 0,
                    "missing_skills": [],
                    "improvements": ["JSON parse error"],
                    "profile_summary": ""
                }
                
    except Exception as e:
        print(f"Analysis error: {e}")  # Debug
        return {
            "score": 0,
            "missing_skills": [],
            "improvements": [f"LLM failed: {str(e)}"],
            "profile_summary": ""
        }
