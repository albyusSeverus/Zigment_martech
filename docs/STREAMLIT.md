# Streamlit UI

Single page app:

- `streamlit/app.py` – Flow Builder only. Create nodes (small boxes), connect them, and click a node to open a popup editor for prompt and per-step model settings.

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

- Add Node to create a box.
- Click Edit on a box to open the popup and set:
  - Label, Output key
  - Prompt template
  - Provider, Model, Temperature, TopP, MaxTokens
- Define connections in the popup or via the Connections list.
- Save Flow to persist to `.streamlit/flows.json`.
