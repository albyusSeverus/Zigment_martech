# ADR 0001: Model defaults and adapters

- Date: 2025-09-14
- Status: Accepted

## Context
We need reliable defaults for side-by-side text generation across Groq and Gemini until per-project presets are added.

## Decision
- Default Groq model: `llama-3.1-70b-versatile` (quality balanced, widely available).
- Default Gemini model: `gemini-2.5-pro`.
- Expose overrides via env vars `GROQ_DEFAULT_MODEL` and `GEMINI_DEFAULT_MODEL`.

## Consequences
- UI can render sensible defaults without extra configuration.
- If accounts expose newer/better models, override via env without code changes.

----

# ADR 0002: Streamlit-only UI and updated defaults

- Date: 2025-09-14
- Status: Accepted

## Context
The project pivoted to a Streamlit-only UI for faster iteration. Provider SDKs and keys were verified. We also aligned defaults with working examples and account availability.

## Decision
- Adopt Streamlit as the only UI in this repo; remove Next.js app code to reduce maintenance.
- Update default models:
  - Groq: `meta-llama/llama-4-scout-17b-16e-instruct`
  - Gemini: `gemini-2.0-flash`
- Load secrets from `.env.local` (or Streamlit secrets) using `python-dotenv` with override on rerun.

## Consequences
- Faster local development and simpler environment.
- Clear env-driven configuration; no hardcoded secrets.
- VS Code tasks/launchers and a Windows script ensure one-click start.
