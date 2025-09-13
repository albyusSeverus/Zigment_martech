## 2025-09-14
Goal: baseline compare working
Changes: scaffolded Next app, added Groq/Gemini adapters, compare + outline + draft APIs, PromptLab skeleton, experiment logging
Results: APIs compile; UI can run compare; defaults set to Groq llama-3.1-70b-versatile and Gemini 2.5 Pro
Next: Outline/Draft UI, diff viewer, RUNLOG wiring from UI

## 2025-09-14 (later)
Goal: simplify to Streamlit-only and verify providers
Changes: removed Next.js app, added Streamlit UI, Start-Streamlit.cmd, VS Code launchers/tasks, dotenv loading; updated defaults to Groq `meta-llama/llama-4-scout-17b-16e-instruct` and Gemini `gemini-2.0-flash`; added docs and checkpoint zip
Results: Internal pings PASS for both providers; double-click and VS Code launch paths working
Next: optional: REST-based Gemini calls; UI polish and usage metrics
