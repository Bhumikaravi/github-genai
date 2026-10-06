from __future__ import annotations

import json
import os
from typing import Dict, Iterator, List

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))


def _gemini_key() -> str | None:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key
    # Streamlit Cloud exposes secrets through st.secrets, not necessarily os.environ.
    try:
        import streamlit as st
        value = st.secrets.get("GEMINI_API_KEY", "")
        return str(value).strip() if value else None
    except Exception:
        return None


def using_cloud_ai() -> bool:
    return bool(_gemini_key())


def check_model() -> tuple[bool, str]:
    """Check the configured AI provider.

    Streamlit Cloud uses Gemini when GEMINI_API_KEY is configured.
    Local development falls back to Ollama when no Gemini key is present.
    """
    if using_cloud_ai():
        return True, f"Cloud AI model '{GEMINI_MODEL}' is ready."

    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        models = [m.get("name", "") for m in response.json().get("models", [])]
        if not any(m == OLLAMA_MODEL or m.startswith(OLLAMA_MODEL + ":") for m in models):
            return False, f"Ollama is running, but model '{OLLAMA_MODEL}' is not installed."
        return True, f"Local model '{OLLAMA_MODEL}' is ready."
    except requests.RequestException:
        return False, (
            f"Cannot connect to Ollama at {OLLAMA_URL}. Start Ollama and try again, "
            "or configure GEMINI_API_KEY for Streamlit Cloud."
        )


def _build_prompt(file_tree: List[str], code_files: Dict[str, str]) -> str:
    tree = "\n".join(file_tree[:200])
    code_parts = []
    for filename, code in code_files.items():
        code_parts.append(f"\n===== {filename} =====\n{code}")
    code = "".join(code_parts)
    return f"""You are a software engineer explaining a GitHub repository to a BCA student.
Use ONLY the repository evidence supplied below. Do not invent features, technologies, files, or behavior.
Write a clear, simple-language explanation with these exact sections:
1. Project Overview
2. Main Features
3. Main Technologies
4. How It Works
5. Important Files
6. How to Run It
7. Beginner-Friendly Summary

Keep it concise but useful. Mention uncertainty when the supplied code is insufficient.

FILE TREE:
{tree}

SOURCE FILES:
{code}
"""


def _stream_ollama(prompt: str) -> Iterator[str]:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        stream=True,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        data = json.loads(line)
        if data.get("error"):
            raise RuntimeError(data["error"])
        chunk = data.get("response", "")
        if chunk:
            yield chunk
        if data.get("done"):
            break


def _stream_gemini(prompt: str, api_key: str) -> Iterator[str]:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("google-genai is not installed. Add it to requirements.txt.") from exc

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=3000,
    )
    try:
        for response in client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        ):
            text = getattr(response, "text", None)
            if text:
                yield text
    except Exception as exc:
        raise RuntimeError(f"Cloud AI request failed: {exc}") from exc


def stream_explanation(file_tree: List[str], code_files: Dict[str, str]) -> Iterator[str]:
    """Stream an explanation from Gemini on Cloud or Ollama locally."""
    prompt = _build_prompt(file_tree, code_files)
    api_key = _gemini_key()
    if api_key:
        yield from _stream_gemini(prompt, api_key)
    else:
        yield from _stream_ollama(prompt)
