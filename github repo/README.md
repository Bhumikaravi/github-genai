# GitHub Repository Code Explainer — Streamlit Cloud Ready

A mini GenAI application that follows:

**GitHub Repository → Code Processing → AI Model → FastAPI Backend → Streamlit Frontend → Explanation**

## What it does

1. Accepts a public GitHub repository URL.
2. Clones the repository with GitPython.
3. Identifies relevant source-code files.
4. Extracts the code with basic file handling.
5. Sends repository evidence to an AI model.
6. Generates a simple, beginner-friendly explanation dynamically.
7. Displays and lets the user download the explanation.

## AI modes

### Streamlit Cloud
Streamlit Cloud cannot access Ollama running on your personal Windows computer. When `GEMINI_API_KEY` is configured in Streamlit Cloud Secrets, this project automatically uses Gemini so the deployed app can generate explanations.

### Local demonstration
If `GEMINI_API_KEY` is not configured, the same project automatically falls back to a locally running Ollama model. This preserves the local-LLM version required for a local demonstration.

## Streamlit Cloud deployment

Use:

- Repository: `Bhumikaravi/github-code-explainers`
- Branch: `main`
- Main file: `frontend/app.py`
- Python: 3.11 or 3.12

In Streamlit Cloud **Advanced settings → Secrets**, add:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Do not commit the key to GitHub.

## Local run with Ollama

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull qwen2.5:3b
python -m streamlit run frontend/app.py
```

The local app uses Ollama when no Gemini key is configured.

## Optional FastAPI backend

```powershell
uvicorn backend.main:app --reload
```

## Project structure

```text
backend/
  __init__.py
  main.py
  services/
    __init__.py
    llm_service.py
    repo_processor.py
frontend/
  app.py
.streamlit/
  config.toml
requirements.txt
README.md
```

## Important note about the assignment

The assignment's local-LLM requirement is satisfied by the Ollama fallback when the project is run locally. The Streamlit Cloud deployment uses Gemini only because a cloud server cannot reach `127.0.0.1:11434` on the student's personal computer.
