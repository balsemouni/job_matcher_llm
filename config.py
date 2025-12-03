import google.generativeai as genai
import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
LLM = None

if not API_KEY:
    st.error("❌ GEMINI_API_KEY environment variable is missing!")
    st.info("Please create a .env file with: GEMINI_API_KEY=your_key_here")
else:
    try:
        genai.configure(api_key=API_KEY)
        LLM = genai.GenerativeModel("gemini-2.5-pro")  # This works for you!
        st.success("✅ Gemini 2.5 Pro configured successfully!")
        print("✅ Gemini 2.5 Pro configured successfully!")
    except Exception as e:
        st.error(f"❌ Failed to configure Gemini: {e}")
        print(f"❌ Configuration error: {e}")
        LLM = None

EMBED_MODEL_NAME = "all-mpnet-base-v2"
CHROMA_PERSIST_DIR = "./chroma_db"