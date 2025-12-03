import streamlit as st
import json
import time
from extraction.pdf_reader import extract_text_from_pdf
from extraction.text_processing import normalize_text, extract_cv_info
from rag.vector_db import store_cv_in_vector_db
from llm.job_analysis import analyze_cv_for_job
from rag.memory import store_memory

st.set_page_config(page_title="AI CV Analyzer (RAG)", layout="wide")
st.title("📄 AI CV Analyzer — RAG + Memory + Vector DB")

# ----------------------------
# PDF Upload
# ----------------------------
uploaded = st.file_uploader("Upload CV (PDF)", type="pdf")

if uploaded:
    cv_path = "temp.pdf"
    with open(cv_path, "wb") as f:
        f.write(uploaded.getbuffer())

    # ----------------------------
    # Extract and normalize text
    # ----------------------------
    raw_text = extract_text_from_pdf(cv_path)
    norm_text = normalize_text(raw_text)
    extracted = extract_cv_info(norm_text)

    # Display extracted info in sidebar
    st.sidebar.header("Extracted Info")
    for k, v in extracted.model_dump().items():
        st.sidebar.write(f"**{k}**")
        st.sidebar.write(v)
        st.sidebar.markdown("---")

    # ----------------------------
    # Index CV
    # ----------------------------
    if st.button("Index CV"):
        n = store_cv_in_vector_db(norm_text)
        st.success(f"Stored {n} chunks")

    # ----------------------------
    # Job Description Input
    # ----------------------------
    jd_text = st.text_area("Job Description", height=250)

    # ----------------------------
    # Stream CV Analysis
    # ----------------------------
    def stream_analyze_cv(cv_text, job_desc, chunk_size=10):
        """Generator that yields CV analysis JSON in word chunks"""
        result = analyze_cv_for_job(cv_text, job_desc)
        json_text = json.dumps(result, indent=2)
        words = json_text.split()
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            yield chunk
            time.sleep(1)  # simulate streaming

    if st.button("Analyze Job Fit"):
        placeholder = st.empty()
        full_text = ""
        store_memory(jd_text, "")  # initialize memory

        for chunk in stream_analyze_cv(norm_text, jd_text):
            full_text += chunk + " "
            placeholder.text(full_text)

        # Store final result in memory
        store_memory(jd_text, full_text)
