import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
import json

from dotenv import load_dotenv
import streamlit as st

try:
    from groq import Groq  # type: ignore
except Exception:  # pragma: no cover
    Groq = None  # type: ignore

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore


# Repo root (two levels up from this file)
REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_FILE = REPO_ROOT / "streamlit" / ".streamlit" / "prompts.json"
FLOW_FILE = REPO_ROOT / "streamlit" / ".streamlit" / "flow.json"


def load_env() -> None:
    # Use override=True so edits to .env.local take effect on rerun
    load_dotenv(REPO_ROOT / ".env", override=True)
    load_dotenv(REPO_ROOT / ".env.local", override=True)


def get_secret(name: str) -> str | None:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name)


def get_default_model(provider: str) -> str:
    if provider.lower() == "groq":
        return os.getenv("GROQ_DEFAULT_MODEL", "llama-3.1-70b-versatile")
    return os.getenv("GEMINI_DEFAULT_MODEL", "gemini-2.0-flash")


def run_groq(prompt: str, system: str | None, model: str, temperature: float, max_tokens: int, top_p: float) -> str:
    api_key = get_secret("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment or Streamlit secrets")
    if Groq is None:
        raise RuntimeError("groq package not installed. Run: pip install -r streamlit/requirements.txt")
    client = Groq(api_key=api_key)
    messages = ([] if not system else [{"role": "system", "content": system}]) + [
        {"role": "user", "content": prompt}
    ]
    res = client.chat.completions.create(
        model=model,
        messages=messages,  # type: ignore[arg-type]
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
    )
    return (res.choices[0].message.content or "").strip()


def run_gemini(prompt: str, system: str | None, model: str, temperature: float, max_tokens: int, top_p: float) -> str:
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment or Streamlit secrets")
    if genai is None:
        raise RuntimeError("google-generativeai not installed. Run: pip install -r streamlit/requirements.txt")
    genai.configure(api_key=api_key)
    mm = genai.GenerativeModel(model_name=model, system_instruction=system)
    res = mm.generate_content(
        prompt,
        generation_config={
            "temperature": float(temperature),
            "max_output_tokens": int(max_tokens),
            "top_p": float(top_p),
        },
    )
    text = ""
    try:
        if getattr(res, "text", None):
            text = res.text  # type: ignore[assignment]
        else:
            r = getattr(res, "response", None)
            if r is not None:
                try:
                    text = r.text()  # type: ignore[assignment]
                except Exception:
                    cands = getattr(r, "candidates", [])
                    if cands:
                        parts = getattr(cands[0].content, "parts", [])
                        if parts:
                            text = getattr(parts[0], "text", "")
    except Exception:
        text = ""
    return (text or "").strip()


def generate(provider: str, prompt: str, system: str | None, model: str, temperature: float, max_tokens: int, top_p: float) -> str:
    if provider.lower() == "groq":
        return run_groq(prompt, system, model, temperature, max_tokens, top_p)
    return run_gemini(prompt, system, model, temperature, max_tokens, top_p)


def sanitize_filename(name: str) -> str:
    s = name.strip().lower().replace(" ", "-")
    return "".join(ch for ch in s if ch.isalnum() or ch in ("-", "_")) or "draft"


def save_markdown(title: str, content: str) -> Path | None:
    base = Path(__file__).resolve().parent.parent
    drafts_dir = base / "content_drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    safe = sanitize_filename(title)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = drafts_dir / f"{safe}-{timestamp}.md"
    content = (content or "").strip()
    if not content:
        return None
    md = f"# {title}\n\n{content}\n"
    path.write_text(md, encoding="utf-8")
    return path


def list_drafts() -> List[Dict[str, Any]]:
    drafts_dir = REPO_ROOT / "content_drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(drafts_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: List[Dict[str, Any]] = []
    for f in files:
        out.append({
            "name": f.name,
            "path": str(f),
            "mtime": f.stat().st_mtime,
        })
    return out


def read_file(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return None


def set_last_output(kind: str, text: str) -> None:
    if kind == "outline":
        st.session_state["last_outline"] = text
    elif kind == "content":
        st.session_state["last_content"] = text


def get_last_outputs() -> Dict[str, str]:
    return {
        "outline": st.session_state.get("last_outline", ""),
        "content": st.session_state.get("last_content", ""),
    }


# Prompt templates management
DEFAULT_PROMPTS = {
    "outline": (
        "You are a senior content strategist. Create a clear, hierarchical outline for a blog about {idea}.\n"
        "Incorporate the following notes if helpful: {notes}.\n"
        "Return Markdown with headings and bullet points only (no full paragraphs)."
    ),
    "blog": (
        "You are a senior content writer. Using the approved outline below, write a comprehensive blog about {idea}.\n\n"
        "Outline:\n{outline}\n\n"
        "Guidelines: follow the outline structure, use an engaging but precise tone, add concrete examples, and end with a concise summary.\n"
        "Output in Markdown."
    ),
}


def _ensure_prompts_file() -> None:
    PROMPTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not PROMPTS_FILE.exists():
        PROMPTS_FILE.write_text(json.dumps(DEFAULT_PROMPTS, indent=2), encoding="utf-8")


def load_prompts() -> Dict[str, str]:
    _ensure_prompts_file()
    try:
        data = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    # Merge with defaults to ensure keys exist
    out = dict(DEFAULT_PROMPTS)
    out.update({k: str(v) for k, v in data.items() if isinstance(v, (str,))})
    return out


def save_prompts(prompts: Dict[str, str]) -> None:
    current = load_prompts()
    current.update({k: str(v) for k, v in prompts.items()})
    PROMPTS_FILE.write_text(json.dumps(current, indent=2), encoding="utf-8")


def format_prompt(template: str, variables: Dict[str, Any]) -> str:
    # Safe formatting: replace missing keys with empty strings
    class SafeDict(dict):
        def __missing__(self, key):
            return ""

    return str(template).format_map(SafeDict(variables))


# Flow management
DEFAULT_FLOW = [
    {
        "label": "Outline",
        "output_key": "outline",
        "template": DEFAULT_PROMPTS["outline"],
    },
    {
        "label": "Blog",
        "output_key": "blog",
        "template": DEFAULT_PROMPTS["blog"],
    },
]


def _ensure_flow_file() -> None:
    FLOW_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not FLOW_FILE.exists():
        FLOW_FILE.write_text(json.dumps(DEFAULT_FLOW, indent=2), encoding="utf-8")


def load_flow() -> List[Dict[str, Any]]:
    _ensure_flow_file()
    try:
        data = json.loads(FLOW_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            # Basic shape validation
            out: List[Dict[str, Any]] = []
            for step in data:
                if not isinstance(step, dict):
                    continue
                label = str(step.get("label", "Step"))
                key = str(step.get("output_key", "step"))
                template = str(step.get("template", ""))
                out.append({"label": label, "output_key": key, "template": template})
            return out or list(DEFAULT_FLOW)
    except Exception:
        pass
    return list(DEFAULT_FLOW)


def save_flow(flow: List[Dict[str, Any]]) -> None:
    # Normalize
    norm: List[Dict[str, Any]] = []
    for s in flow:
        norm.append({
            "label": str(s.get("label", "Step")),
            "output_key": str(s.get("output_key", "step")),
            "template": str(s.get("template", "")),
        })
    FLOW_FILE.write_text(json.dumps(norm, indent=2), encoding="utf-8")
