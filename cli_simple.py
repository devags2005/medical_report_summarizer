import os, sys, re
from openai import OpenAI

def basic_anonymize(text: str) -> str:
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
    text = re.sub(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){1,2}\d{3,4}\b", "[PHONE]", text)
    text = re.sub(r"\b(?:\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2})\b", "[DATE]", text)
    return text

def build_prompt(text: str) -> str:
    return f"""Summarize the medical report in 5 simple lines for a patient.
- Use very simple words.
- Do not add facts not in the text.
- If not present, say 'Not mentioned'.

Text:
{text}
"""

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli_simple.py <path_to_text_file>")
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Set environment variable OPENAI_API_KEY first.")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        raw = f.read()

    raw = basic_anonymize(raw)
    prompt = build_prompt(raw)

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": "You summarize medical reports safely."},
            {"role": "user", "content": prompt}
        ]
    )
    print("\n--- SUMMARY ---\n")
    print(resp.choices[0].message.content.strip())

if __name__ == "__main__":
    main()
