from __future__ import annotations

import json
import os
from typing import Dict, Iterator, List

import requests


# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:3b"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)

TIMEOUT = int(
    os.getenv("OLLAMA_TIMEOUT", "180")
)


# ============================================================
# GEMINI API KEY
# ============================================================

def _gemini_key() -> str | None:
    """
    Get Gemini API key.

    Priority:
    1. Environment variable
    2. Streamlit Secrets
    """

    # Check environment variable
    key = os.getenv("GEMINI_API_KEY", "").strip()

    if key:
        return key

    # Check Streamlit Cloud secrets
    try:
        import streamlit as st

        value = st.secrets.get(
            "GEMINI_API_KEY",
            ""
        )

        if value:
            return str(value).strip()

    except Exception:
        pass

    return None


# ============================================================
# CHECK AI PROVIDER
# ============================================================

def using_cloud_ai() -> bool:
    """
    Returns True when Gemini API key is available.
    """

    return bool(_gemini_key())


def check_model() -> tuple[bool, str]:
    """
    Check whether the AI provider is available.

    Streamlit Cloud:
        Gemini

    Local computer:
        Ollama
    """

    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    if using_cloud_ai():

        return (
            True,
            f"Cloud AI model '{GEMINI_MODEL}' is ready."
        )

    # --------------------------------------------------------
    # OLLAMA
    # --------------------------------------------------------

    try:

        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=5
        )

        response.raise_for_status()

        data = response.json()

        models = [
            model.get("name", "")
            for model in data.get("models", [])
        ]

        # Exact model or model with tag
        model_available = any(
            model == OLLAMA_MODEL
            or model.startswith(
                OLLAMA_MODEL + ":"
            )
            for model in models
        )

        if not model_available:

            return (
                False,
                f"Ollama is running, but model "
                f"'{OLLAMA_MODEL}' is not installed."
            )

        return (
            True,
            f"Local model '{OLLAMA_MODEL}' is ready."
        )

    except requests.RequestException:

        return (
            False,
            f"Cannot connect to Ollama at "
            f"{OLLAMA_URL}. Start Ollama and try again, "
            "or configure GEMINI_API_KEY for Streamlit Cloud."
        )


# ============================================================
# BUILD PROMPT
# ============================================================

def _build_prompt(
    file_tree: List[str],
    code_files: Dict[str, str]
) -> str:

    # Limit file tree
    tree = "\n".join(
        file_tree[:200]
    )

    code_parts = []

    for filename, code in code_files.items():

        code_parts.append(
            f"\n===== {filename} =====\n{code}"
        )

    code = "".join(code_parts)

    prompt = f"""
You are a software engineer explaining a GitHub repository
to a BCA student.

Use ONLY the repository evidence supplied below.

Do NOT invent:
- features
- technologies
- files
- functionality
- APIs
- databases
- frameworks

If something cannot be determined from the supplied code,
clearly say that it is not available in the provided files.

Write a clear and simple explanation using EXACTLY these
sections:

1. Project Overview
2. Main Features
3. Main Technologies
4. How It Works
5. Important Files
6. How to Run It
7. Beginner-Friendly Summary

Keep the explanation concise but useful.

FILE TREE:
{tree}

SOURCE FILES:
{code}
"""

    return prompt


# ============================================================
# OLLAMA STREAM
# ============================================================

def _stream_ollama(
    prompt: str
) -> Iterator[str]:

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.2,
            "num_ctx": 8192
        }
    }

    try:

        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            stream=True,
            timeout=TIMEOUT
        )

        response.raise_for_status()

    except requests.RequestException as exc:

        raise RuntimeError(
            f"Could not connect to Ollama: {exc}"
        ) from exc

    # Read streamed response
    for line in response.iter_lines(
        decode_unicode=True
    ):

        if not line:
            continue

        try:

            data = json.loads(line)

        except json.JSONDecodeError:

            continue

        # Ollama error
        if data.get("error"):

            raise RuntimeError(
                data["error"]
            )

        # Generated text
        chunk = data.get(
            "response",
            ""
        )

        if chunk:

            yield chunk

        # Generation finished
        if data.get("done"):

            break


# ============================================================
# GEMINI STREAM
# ============================================================

def _stream_gemini(
    prompt: str,
    api_key: str
) -> Iterator[str]:

    # --------------------------------------------------------
    # IMPORT GOOGLE GENAI
    # --------------------------------------------------------

    try:

        from google import genai
        from google.genai import types

    except ImportError as exc:

        raise RuntimeError(
            f"Google GenAI SDK import failed: {exc}. "
            "Make sure 'google-genai' is present "
            "in requirements.txt."
        ) from exc

    # --------------------------------------------------------
    # CREATE CLIENT
    # --------------------------------------------------------

    try:

        client = genai.Client(
            api_key=api_key
        )

    except Exception as exc:

        raise RuntimeError(
            f"Could not create Gemini client: {exc}"
        ) from exc

    # --------------------------------------------------------
    # GENERATION CONFIG
    # --------------------------------------------------------

    config = types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=3000
    )

    # --------------------------------------------------------
    # GENERATE RESPONSE
    # --------------------------------------------------------

    try:

        responses = client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config
        )

        for response in responses:

            text = getattr(
                response,
                "text",
                None
            )

            if text:

                yield text

    except Exception as exc:

        raise RuntimeError(
            f"Cloud AI request failed: {exc}"
        ) from exc


# ============================================================
# MAIN EXPLANATION FUNCTION
# ============================================================

def stream_explanation(
    file_tree: List[str],
    code_files: Dict[str, str]
) -> Iterator[str]:
    """
    Generate repository explanation.

    If GEMINI_API_KEY exists:
        Use Gemini.

    Otherwise:
        Use local Ollama.
    """

    # Build prompt
    prompt = _build_prompt(
        file_tree,
        code_files
    )

    # Get Gemini API key
    api_key = _gemini_key()

    # --------------------------------------------------------
    # STREAMLIT CLOUD → GEMINI
    # --------------------------------------------------------

    if api_key:

        yield from _stream_gemini(
            prompt,
            api_key
        )

        return

    # --------------------------------------------------------
    # LOCAL COMPUTER → OLLAMA
    # --------------------------------------------------------

    yield from _stream_ollama(
        prompt
    )
