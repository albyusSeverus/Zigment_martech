import os
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[1]
if load_dotenv:
    # Load keys from .env/.env.local if present
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(REPO_ROOT / ".env.local")


def ping_groq() -> tuple[bool, str]:
    try:
        from groq import Groq
    except Exception as e:  # noqa: BLE001
        return False, f"groq import failed: {e}"

    key = os.getenv("GROQ_API_KEY")
    if not key:
        return False, "GROQ_API_KEY missing"

    model = os.getenv("GROQ_DEFAULT_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    try:
        t0 = time.time()
        client = Groq(api_key=key)
        res = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'pong'"}],
            temperature=0,
            max_tokens=8,
        )
        dt = (time.time() - t0) * 1000
        text = (res.choices[0].message.content or "").strip()
        ok = bool(text)
        return ok, f"{model} {dt:.0f}ms -> {text[:80]!r}"
    except Exception as e:  # noqa: BLE001
        return False, f"error: {e}"


def ping_gemini() -> tuple[bool, str]:
    try:
        import google.generativeai as genai
    except Exception as e:  # noqa: BLE001
        return False, f"google-generativeai import failed: {e}"

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return False, "GEMINI_API_KEY missing"

    model = os.getenv("GEMINI_DEFAULT_MODEL", "gemini-2.0-flash")
    try:
        t0 = time.time()
        genai.configure(api_key=key)
        mm = genai.GenerativeModel(model_name=model)
        res = mm.generate_content(
            "Return the word pong",
            generation_config={
                "temperature": 0,
                "max_output_tokens": 8,
                "top_p": 1,
            },
        )
        dt = (time.time() - t0) * 1000
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
        text = (text or "").strip()
        ok = True  # treat as reachable even if empty text
        return ok, f"{model} {dt:.0f}ms -> {text[:80]!r}"
    except Exception as e:  # noqa: BLE001
        return False, f"error: {e}"


def main() -> int:
    results = []
    ok_groq, msg_groq = ping_groq()
    results.append(("GROQ", ok_groq, msg_groq))
    ok_gem, msg_gem = ping_gemini()
    results.append(("GEMINI", ok_gem, msg_gem))

    for name, ok, msg in results:
        status = "PASS" if ok else "FAIL"
        print(f"{name}: {status} - {msg}")

    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
