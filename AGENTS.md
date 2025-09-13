# AGENTS — Working in this Repo

Scope: entire repository.

Read this first if you are an automated coding agent (Codex/CLI or similar).

1) Guardrails
- Prefer editing or adding docs in `docs/` and adding non-invasive helper scripts.
- Never commit secrets. Use Streamlit secrets or environment variables.

2) Orientation
- Start with `docs/CODEX.md` for an overview of structure, run commands, env, and common tasks.
- Streamlit UI lives under `streamlit/`. Drafts are written to `content_drafts/`.

3) Running
- Streamlit: `streamlit run streamlit/app.py` (or launcher: "Start UI (Streamlit)").

4) Docs
- Add project notes, ADRs, onboarding, and runbooks to `docs/`.
- See `docs/CODEX.md` for details.
