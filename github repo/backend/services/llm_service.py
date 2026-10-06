from __future__ import annotations

import os
from typing import Dict, Iterator, List

import requests


GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


def get_gemini_key() -> str | None:
    """
    Gets Gemini API key from:
    1. Environment variable
    2. Streamlit Secrets
    """

    key = os.getenv("GEMINI_API_KEY", "").strip()

    if key:
        return key

    try:
        import streamlit as st

        key = st.secrets.get(
            "GEMINI_API_KEY",
            ""
        )

        if key:
            return str(key).strip()

    except Exception:
        pass

    return None


def check_model() -> tuple[bool, str]:
    """
    Checks whether Gemini API key is configured.
    """

    key = get_gemini_key()

    if not key:
        return (
            False,
            "Gemini API key is not configured."
        )

    return (
        True,
        f"Gemini model '{GEMINI_MODEL}' is ready."
    )


def _build_prompt(
    file_tree: List[str],
    code_files: Dict[str, str],
) -> str:

    tree = "\n".join(file_tree[:200])

    code_parts = []

    for filename, code in code_files.items():
        code_parts.append(
            f"\n===== {filename} =====\n{code}"
        )

    code = "".join(code_parts)

    return f"""
You are a software engineer explaining a GitHub
repository to a BCA student.

Analyze ONLY the repository information provided below.

Do not invent:
- features
- technologies
- files
- APIs
- databases
- frameworks
- functionality

If something cannot be determined from the provided
repository files, clearly say that it cannot be determined.

Explain the project in simple and clear English.

Use EXACTLY these sections:

# 1. Project Overview

Explain what the project does.

# 2. Main Features

List the important features visible from the code.

# 3. Main Technologies

Mention programming languages, libraries,
frameworks and tools actually found in the files.

# 4. How It Works

Explain the flow step by step.

# 5. Important Files

Mention important files and explain their purpose.

# 6. How to Run It

Explain how the project can be run based only
on the available files.

# 7. Beginner-Friendly Summary

Give a simple explanation suitable for a BCA student.

Keep the explanation concise and useful.

================ FILE TREE ================

{tree}

================ SOURCE FILES ================

{code}
"""


def _generate_with_gemini(
    prompt: str,
    api_key: str,
) -> Iterator[str]:

    try:
        from google import genai

    except Exception as exc:

        raise RuntimeError(
            "Gemini SDK could not be imported. "
            "Make sure google-genai is installed. "
            f"Import error: {exc}"
        ) from exc

    try:

        client = genai.Client(
            api_key=api_key
        )

    except Exception as exc:

        raise RuntimeError(
            f"Could not create Gemini client: {exc}"
        ) from exc

    try:

        response_stream = (
            client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=prompt,
            )
        )

        for response in response_stream:

            text = getattr(
                response,
                "text",
                None,
            )

            if text:
                yield text

    except Exception as exc:

        raise RuntimeError(
            f"Gemini request failed: {exc}"
        ) from exc


def stream_explanation(
    file_tree: List[str],
    code_files: Dict[str, str],
) -> Iterator[str]:

    api_key = get_gemini_key()

    if not api_key:
        raise RuntimeError(
            "Gemini API key is missing. "
            "Add GEMINI_API_KEY in Streamlit Secrets."
        )

    prompt = _build_prompt(
        file_tree,
        code_files,
    )

    yield from _generate_with_gemini(
        prompt,
        api_key,
    )
