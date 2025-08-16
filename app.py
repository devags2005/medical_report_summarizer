import streamlit as st
import nltk
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline, Pipeline
import torch
import re
from typing import List

# Download required NLTK resources
nltk.download('punkt')
nltk.download('punkt_tab')

# ---------------------------
# Streamlit Page Config
# ---------------------------
st.set_page_config(page_title="Medical Report Summarizer", layout="wide")
st.markdown("""
<style>
body {
    background-color: #1e1e1e;
    color: #f5f5f5;
}
.title {
    font-size: 2.2em;
    text-align: center;
    color: #00c4ff;
    font-weight: bold;
    margin-bottom: 20px;
}
.summary-box {
    background-color: #292929;
    padding: 15px;
    border-radius: 10px;
    color: #f5f5f5;
    font-size: 1.05em;
    border: 1px solid #00c4ff;
}
.stat-card {
    background-color: #333333;
    padding: 12px;
    border-radius: 8px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='title'>🩺 Medical Report Summarizer</h1>", unsafe_allow_html=True)

# ---------------------------
# Utility Functions
# ---------------------------
def split_into_sentences(text: str) -> List[str]:
    return nltk.sent_tokenize(text)

def extractive_textrank(text: str, num_sentences: int = 3) -> str:
    sentences = split_into_sentences(text)
    if len(sentences) <= num_sentences:
        return text

    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(sentences)
    similarity_graph = (tfidf_matrix * tfidf_matrix.T).toarray()

    nx_graph = nx.from_numpy_array(similarity_graph)
    scores = nx.pagerank(nx_graph)

    ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
    top_sentences = [s for _, s in ranked_sentences[:num_sentences]]
    return " ".join(top_sentences)

# ---------------------------
# Hugging Face Pipeline Loader
# ---------------------------
@st.cache_resource(show_spinner=False)
def load_abstractive_pipeline() -> Pipeline | None:
    try:
        device = 0 if torch.cuda.is_available() else -1
        return pipeline("summarization", model="facebook/bart-large-cnn", device=device)
    except Exception:
        return None

summarizer = load_abstractive_pipeline()

def abstractive_summarize(text: str, chunk_size: int = 350, overlap: int = 20) -> str:
    chunks = chunk_text(text, words_per_chunk=chunk_size, overlap=overlap)
    summaries = []

    progress = st.progress(0)
    for i, chunk in enumerate(chunks):
        try:
            summary = summarizer(chunk, max_length=130, min_length=40, do_sample=False)[0]['summary_text']
            summaries.append(summary)
        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                st.error("⚠️ GPU out of memory. Try reducing chunk size or use Extractive mode.")
                return ""
            else:
                st.error(str(e))
                return ""
        progress.progress((i + 1) / len(chunks))
    return " ".join(summaries)

def chunk_text(text: str, words_per_chunk: int = 350, overlap: int = 20) -> List[str]:
    words = text.split()
    if len(words) <= words_per_chunk:
        return [" ".join(words)]
    chunks = []
    step = int(words_per_chunk * (1 - overlap / 100))
    i = 0
    while i < len(words):
        chunk = words[i: i + words_per_chunk]
        chunks.append(" ".join(chunk))
        i += step
    return chunks

# ---------------------------
# Sidebar Controls
# ---------------------------
st.sidebar.header("⚙️ Settings")
mode = st.sidebar.radio("Select Summarization Type", ["Extractive", "Abstractive"])

if mode == "Abstractive":
    chunk_size = st.sidebar.slider("Chunk size (words)", 200, 600, 350, step=50)
    overlap = st.sidebar.slider("Chunk overlap (%)", 0, 50, 20, step=5)

if torch.cuda.is_available():
    st.sidebar.caption(f"GPU: {torch.cuda.get_device_name(0)}")
else:
    st.sidebar.caption("Running on CPU")

# ---------------------------
# Input Section
# ---------------------------
st.subheader("Upload Medical Report or Paste Text")
uploaded_file = st.file_uploader("Upload .txt file", type=["txt"])
text = ""

if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8")
else:
    text = st.text_area("Enter medical report text here", height=250)

if st.button("Load Sample Medical Report"):
    text = """Patient Name: John Doe
Age: 45
Gender: Male
Diagnosis: Type 2 Diabetes Mellitus
Medications: Metformin 500mg twice daily
Lab Results: Fasting blood glucose - 145 mg/dL, HbA1c - 7.8%
Plan: Continue Metformin, start lifestyle modifications, follow-up in 3 months.
"""

if text.strip():
    st.subheader("Summary Options")
    sent_count = st.slider("Number of sentences (for Extractive)", 2, 10, 3)

    if st.button("Generate Summary"):
        with st.spinner("Summarizing..."):
            if mode == "Extractive":
                summary = extractive_textrank(text, num_sentences=sent_count)
            else:
                summary = abstractive_summarize(text, chunk_size=chunk_size, overlap=overlap)

        if summary:
            st.subheader("📄 Summary")
            with st.expander("View Summary", expanded=True):
                st.markdown(f"<div class='summary-box'>{summary}</div>", unsafe_allow_html=True)

            st.download_button("📥 Download Summary", summary, file_name="summary.txt")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div class='stat-card'><b>Original:</b> {len(text.split())} words</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='stat-card'><b>Summary:</b> {len(summary.split())} words</div>", unsafe_allow_html=True)
            with col3:
                ratio = len(summary.split()) / len(text.split()) * 100
                st.markdown(f"<div class='stat-card'><b>Compression:</b> {ratio:.1f}%</div>", unsafe_allow_html=True)
else:
    st.info("Please upload a file or enter text to summarize.")
