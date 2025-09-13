Content Engine — Streamlit UI Only

This repo provides a Streamlit UI to compare Groq and Gemini outputs, preview content, and save drafts to `content_drafts/`.

Quick start

- Python 3.9+
- `pip install -r streamlit/requirements.txt`
- `streamlit run streamlit/app.py`

Provide API keys via environment or Streamlit secrets:

- Env vars: `GROQ_API_KEY`, `GEMINI_API_KEY`
- Or copy `streamlit/.streamlit/secrets.toml.example` → `streamlit/.streamlit/secrets.toml` and fill values.

One-click on Windows: double-click `Start-Streamlit.cmd`.

VS Code

- Run and Debug → "Start UI (Streamlit)" (or the parent-workspace variant)
- Terminal → Run Task → "Run Streamlit (cmd)" (or the parent-workspace variant)

Defaults and keys

- Defaults: Groq `meta-llama/llama-4-scout-17b-16e-instruct`, Gemini `gemini-2.0-flash`
- Configure in `.env.local`: `GROQ_API_KEY`, `GEMINI_API_KEY` (and optionally override defaults)

Docs

- See `docs/STREAMLIT.md` for full instructions.
- See `docs/CODEX.md` for agent onboarding/guardrails.
