# Streamlit UI

Two pages:

- `streamlit/app.py` – Content Generator (runs your configured flow: choose model, idea → Generate steps).
- `streamlit/pages/Prompts.py` – Flow Builder to design/edit the ordered steps and their prompt templates.

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

- Open `Prompts` to configure the flow. For each step, set:
  - Label: display name.
  - Output key: how later steps reference this step’s output (e.g., `outline`).
  - Template: the prompt text (variables available: `{idea}`, `{notes}`, plus prior step outputs by their output key, e.g. `{outline}`).
- In `Content Generator`, pick provider/model and enter Idea + Notes.
- Click `Generate All` or run a specific step from the dropdown.
