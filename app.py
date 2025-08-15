import re
import streamlit as st
import pdfplumber
from transformers import pipeline
from fpdf import FPDF

# ---------------------------- Load Summarizer ----------------------------
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

summarizer = load_summarizer()

# ---------------------------- Helper Functions ----------------------------
def extract_text_from_pdf(uploaded_file) -> str:
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        text = "\n".join(pages).strip()
        if not text:
            return "ERROR: PDF contains no readable text."
        return text
    except Exception as e:
        return f"ERROR: Could not read PDF. Details: {e}"

def basic_anonymize(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
    text = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){1,2}\d{3,4}\b", "[PHONE]", text)
    text = re.sub(r"\b(?:\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2})\b", "[DATE]", text)
    text = re.sub(r"\b(MRN[:\s]*\d{5,}|Record\s*No[:\s]*\d{5,})\b", "[MRN]", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(Name|Patient Name|Pt\. Name)\s*:\s*[\w ,.'-]+\b", r"\1: [NAME]", text, flags=re.IGNORECASE)
    return text

def _phrase(tone: str, patient: str, doctor: str) -> str:
    return patient if tone == "Patient" else doctor

def call_huggingface_summary_paragraph(text: str, tone: str, original_text: str) -> str:
    """
    Generate a paragraph-style summary with Patient/Doctor tone.
    """
    # Extract basic info
    patient_name = "Not mentioned"
    age_gender = ""
    complaint = "Not mentioned"
    diagnosis = "Not mentioned"
    procedure = "Not mentioned"
    outcome = "Not mentioned"
    meds = ""
    follow_up = ""

    # Patient info
    match_name = re.search(r"Patient Name\s*:\s*([\w ,.'-]+)", original_text, re.IGNORECASE)
    if match_name:
        patient_name = match_name.group(1).strip()
    match_age = re.search(r"Age\s*:\s*(\d{1,3})", original_text, re.IGNORECASE)
    match_gender = re.search(r"(Male|Female)", original_text, re.IGNORECASE)
    if match_age:
        age_gender = f"{match_age.group(1)} years"
    if match_gender:
        age_gender += f", {match_gender.group(1)}"

    # Complaint
    complaint_match = re.search(r"(Chief Complaint\s*:\s*.+)", original_text, re.IGNORECASE)
    if complaint_match:
        complaint = complaint_match.group(1).split(":",1)[1].strip()

    # Diagnosis
    orig_low = original_text.lower()
    if "st elevation" in orig_low and "troponin" in orig_low and "positive" in orig_low:
        diagnosis = "Heart attack" if tone=="Patient" else "Acute myocardial infarction (STEMI)"
    elif "angina" in orig_low:
        diagnosis = "Chest pain likely due to angina" if tone=="Patient" else "Stable angina"
    elif "pneumonia" in orig_low:
        diagnosis = "Pneumonia"

    # Procedure
    procedure_match = re.search(r"(Procedure\s*:\s*.+)", original_text, re.IGNORECASE)
    if procedure_match:
        procedure = procedure_match.group(1).split(":",1)[1].strip()

    # Outcome
    outcome_match = re.search(r"(discharge[d]?|stable|recovered|improved).*?(\.|,|\n)", original_text, re.IGNORECASE)
    if outcome_match:
        outcome = outcome_match.group(0).strip()

    # Medications
    meds_match = re.search(r"(Medications\s*:\s*.+)", original_text, re.IGNORECASE)
    if meds_match:
        meds = meds_match.group(1).split(":",1)[1].strip()
    follow_up_match = re.search(r"(Follow[- ]?up\s*:\s*.+)", original_text, re.IGNORECASE)
    if follow_up_match:
        follow_up = follow_up_match.group(1).split(":",1)[1].strip()

    # Build paragraph dynamically based on tone
    if tone == "Patient":
        paragraph = f"{patient_name}"
        if age_gender:
            paragraph += f", {age_gender}"
        paragraph += f", experienced {complaint}. "
        if diagnosis != "Not mentioned":
            paragraph += f"This was diagnosed as {diagnosis}. "
        if procedure != "Not mentioned":
            paragraph += f"The treatment performed was {procedure}. "
        if outcome != "Not mentioned":
            paragraph += f"The outcome was {outcome}. "
        if meds:
            paragraph += f"Medications prescribed include {meds}. "
        if follow_up:
            paragraph += f"Follow-up is scheduled: {follow_up}."
    else:  # Doctor tone
        paragraph = f"Patient: {patient_name}"
        if age_gender:
            paragraph += f", {age_gender}"
        paragraph += f". Chief complaint: {complaint}. "
        if diagnosis != "Not mentioned":
            paragraph += f"Diagnosis: {diagnosis}. "
        if procedure != "Not mentioned":
            paragraph += f"Procedure/Treatment: {procedure}. "
        if outcome != "Not mentioned":
            paragraph += f"Outcome: {outcome}. "
        if meds:
            paragraph += f"Medications: {meds}. "
        if follow_up:
            paragraph += f"Follow-up: {follow_up}."

    return paragraph

def create_pdf_paragraph(summary_text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", size=16)
    pdf.set_text_color(0, 0, 128)
    pdf.cell(200, 10, "Medical Report Summary", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 8, summary_text)
    return pdf.output(dest='S').encode('latin1')

# ---------------------------- UI ----------------------------
st.set_page_config(page_title="Medical Report Summarizer", page_icon="🩺")
st.title("🩺 Medical Report Summarizer")

mask_phi = st.checkbox("Mask personal details before summarizing", value=True)
tone = st.radio("Select Summary Tone", ["Patient", "Doctor"], index=0)
mode = st.radio("Input Method", ["Paste Text", "Upload PDF", "Use Sample"], index=0)

raw_text = ""
if mode == "Paste Text":
    raw_text = st.text_area("Paste your medical report text here:", height=220)
elif mode == "Upload PDF":
    uploaded_file = st.file_uploader("Upload a medical report PDF", type=["pdf"])
    if uploaded_file is not None:
        raw_text = extract_text_from_pdf(uploaded_file)
elif mode == "Use Sample":
    raw_text = """Patient Name: John Smith
Age: 65 years
History: Hypertension, high cholesterol
Chief Complaint: Severe chest pain for 4 hours radiating to left arm with sweating
ECG: ST elevation in leads II, III, aVF
Troponin: Positive
Procedure: PCI with stent in RCA
Medications: Aspirin, Clopidogrel, Statin, Metoprolol
Follow-up: Cardiology OPD after 2 weeks
Outcome: Patient discharged in stable condition"""

if st.button("✨ Summarize"):
    if not raw_text or raw_text.startswith("ERROR"):
        st.error("Please provide valid text or a readable PDF.")
    else:
        text_to_summarize = basic_anonymize(raw_text) if mask_phi else raw_text
        with st.spinner("Generating paragraph-style summary..."):
            summary = call_huggingface_summary_paragraph(text_to_summarize, tone, raw_text)

        st.subheader("📝 Summary")
        st.write(summary)

        st.download_button("⬇️ Download as TXT", summary.encode("utf-8"), "summary.txt")
        st.download_button("⬇️ Download as PDF", create_pdf_paragraph(summary), "summary.pdf")
