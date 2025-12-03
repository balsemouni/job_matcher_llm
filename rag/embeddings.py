from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import streamlit as st
from config import EMBED_MODEL_NAME

try:
    #Load the embedding model
    embed_model = SentenceTransformer(EMBED_MODEL_NAME)
except Exception:
    embed_model = None
    st.warning("Embedding model could not load.")
#creates a function that splits text into smaller pieces.
def chunk_text(text, chunk_size=500, overlap=50):
    # overlap le nombre de caractères répétés d’un chunk au suivant.Cela sert à AIDER l'IA à garder le CONTEXTE entre les morceaux.
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        return splitter.split_text(text)
    except:
        return [text]
