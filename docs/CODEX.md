# Codex Onboarding — Content Engine

This document gives Codex (the coding agent) the minimum context needed to work productively in this repo. The project is now Streamlit‑only.

## Mission

- Compare Groq and Gemini model outputs side‑by‑side, develop outlines and drafts, and save results to `content_drafts/`.
- Frontend: Streamlit under `streamlit/`.

## Directories & Key Files

- `content_drafts/` — Markdown drafts are saved here.
- `docs/` — Project notes. This file (CODEX.md) lives here.
- See also `docs/CHECKPOINTS.md` for restorable snapshots.
- `streamlit/` — Streamlit UI (Python), writes to `content_drafts/`.
- `.vscode/launch.json` — One‑click launcher for Streamlit.

## Runbook

- Streamlit UI
  - Keys: set env vars or create `streamlit/.streamlit/secrets.toml` (see `secrets.toml.example`).
  - Install: `pip install -r streamlit/requirements.txt`.
  - Start: `streamlit run streamlit/app.py` (or use launcher “Start UI (Streamlit)” or `Start-Streamlit.cmd`).

## Guardrails (Very Important)

- Prefer creating or updating docs in `docs/`, or adding non-invasive helpers (scripts).
- Never hardcode API keys in source. Use Streamlit secrets or environment variables.
- Keep changes small, focused, and consistent with existing style.

## Environment Variables

- `GROQ_API_KEY` — Groq SDK key.
- `GEMINI_API_KEY` — Google Generative AI key.
- `GROQ_DEFAULT_MODEL` — default Groq model (default: `llama-3.1-70b-versatile`).
- `GEMINI_DEFAULT_MODEL` — default Gemini model (default: `gemini-2.5-pro`).

## APIs (summary)

API routes were part of the Next.js app and have been removed in this Streamlit‑only setup.

## Typical Tasks for Codex

- Add docs: put onboarding, notes, and decisions into `docs/`.
- Add helpers: scripts and VS Code launchers are acceptable.
- Implement features in `streamlit/`; keep writes confined to `content_drafts/`.

## Quick Checks

- If requests to Groq/Gemini fail: confirm keys in `.env.local` (Next.js) or secrets/env (Streamlit).
- If saving drafts fails: ensure `content_drafts/` is writable; the server process must have permissions.

## Notes

- Build artifacts like `.next/` and dependencies like `node_modules/` should not be committed. They can exist locally.
- `.env.local` is ignored by git by default here.
