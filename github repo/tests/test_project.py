import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_required_files_exist():
    required = [
        "backend/main.py",
        "backend/services/repo_processor.py",
        "backend/services/llm_service.py",
        "frontend/app.py",
        "requirements.txt",
    ]
    assert all((ROOT / p).exists() for p in required)


def test_prompt_has_required_sections():
    from backend.services.llm_service import _build_prompt

    prompt = _build_prompt(["main.py"], {"main.py": "print('hello')"})
    for section in [
        "Project Overview",
        "Main Features",
        "Main Technologies",
        "How It Works",
        "Important Files",
        "How to Run It",
        "Beginner-Friendly Summary",
    ]:
        assert section in prompt


def test_cloud_provider_detection(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    from backend.services import llm_service
    assert llm_service.using_cloud_ai() is True
