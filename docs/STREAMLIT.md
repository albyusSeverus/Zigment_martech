# Streamlit UI

Two simple pages:

- `streamlit/app.py` – Content Generator (choose model, idea → Generate Outline → Generate Blog).
- `streamlit/pages/Prompts.py` – Prompt Manager to edit base templates for Outline and Blog.

## Setup

1) Provide API keys via environment or Streamlit secrets.

PowerShell example:

```
$env:GROQ_API_KEY="..."
$env:GEMINI_API_KEY="..."
```

Or create `streamlit/.streamlit/secrets.toml`:

```toml
[secrets]
GROQ_API_KEY = "your_groq_key"
GEMINI_API_KEY = "your_gemini_key"
```

2) Install dependencies:

```
pip install -r streamlit/requirements.txt
```

3) Run the app:

```
streamlit run streamlit/app.py
```

## Defaults

- Groq model from `GROQ_DEFAULT_MODEL` (fallback `llama-3.1-70b-versatile`).
- Gemini model from `GEMINI_DEFAULT_MODEL` (fallback `gemini-2.0-flash`).

## Usage

- Open `Prompts` to configure templates. Variables:
  - Outline: `{idea}`, `{notes}`
  - Blog: `{idea}`, `{notes}`, `{outline}`
- In `Content Generator`, pick provider/model, enter an idea + optional notes, click `Generate Outline`.
- If satisfied, click `Generate Blog`.

