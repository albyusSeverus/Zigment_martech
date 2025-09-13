# Checkpoints

This file tracks restorable checkpoints (zip snapshots) of the project.

## 2025-09-14 — Streamlit-only baseline

- State: Streamlit UI only, Groq + Gemini configured via `.env.local`.
- Defaults:
  - GROQ_DEFAULT_MODEL: `meta-llama/llama-4-scout-17b-16e-instruct`
  - GEMINI_DEFAULT_MODEL: `gemini-2.0-flash`
- Keys expected in `.env.local`:
  - `GROQ_API_KEY`
  - `GEMINI_API_KEY`
- Launchers:
  - Windows: `Start-Streamlit.cmd`
  - VS Code: Run and Debug → "Start UI (Streamlit)" or Tasks → "Run Streamlit (cmd)"
- Drafts: saved to `content_drafts/`

To restore from zip: extract over the project folder or into a new folder.

