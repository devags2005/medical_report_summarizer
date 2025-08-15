# 🩺 Medical Report Summarizer (Demo)

> **Goal:** Paste or upload a medical report → get a short, clear summary for a **Patient** or a **Doctor**.  
> **Note:** This is for **learning only**. Do **not** use for real medical decisions.

---

## 🧒 Super-Simple Plan (like for 5th standard)

1. **Install Python** (version 3.9+).
2. Open **Terminal / Command Prompt**.
3. Go to this project folder.
4. Type: `pip install -r requirements.txt`
5. Get your **OpenAI API Key** from https://platform.openai.com/
6. **Run the app:** `streamlit run app.py`
7. Paste some report text, or upload a PDF → click **Summarize**.

That’s it! 🎉

---

## 🔑 Set API Key (2 ways)

- **Inside the app**: Paste the key in the text box (easiest).  
- **Or via environment** (Windows PowerShell):
  ```powershell
  setx OPENAI_API_KEY "your_key_here"
  ```
  **macOS/Linux (bash/zsh):**
  ```bash
  export OPENAI_API_KEY="your_key_here"
  ```

---

## 🧪 Try with Sample Text

Click **Use Sample** in the app. A fake (dummy) discharge summary is provided.

---

## 🧠 What this shows (matches the JD)

- **LLM Summarization** of medical reports (Generative AI ✅)
- **Simple PHI masking** before sending to the model (privacy ✅)
- **Doctor vs Patient** tone (NLP prompt design ✅)
- **PDF text extraction** (data handling ✅)

---

## 🛡️ Safety Notes

- Demo only. Not medical advice.
- Do not upload real patient data.
- The PHI masking here is **basic**. Real systems need much stronger privacy tools.

---

## 🧰 CLI (terminal) Version

1. Put your text report in a file, e.g., `report.txt`.
2. Set env var:  
   - Windows: `setx OPENAI_API_KEY "your_key"`  
   - macOS/Linux: `export OPENAI_API_KEY="your_key"`
3. Run:  
   ```bash
   python cli_simple.py report.txt
   ```

---

## ✅ Quick Checklist for Demo Day

- [ ] Show **Patient** summary (simple words).  
- [ ] Show **Doctor** summary (headings + clinical terms).  
- [ ] Tick "**Mask personal details**" to show privacy awareness.  
- [ ] Use a PDF and show it still works.  
- [ ] End with “This is a demo, not medical advice.”

Good luck! 🚀
