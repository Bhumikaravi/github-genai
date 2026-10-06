from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List

from git import Repo

IGNORED_DIRS = {
    ".git", ".github", "node_modules", "venv", ".venv", "env", "__pycache__",
    ".pytest_cache", ".mypy_cache", "dist", "build", "coverage", ".idea", ".vscode"
}
SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rs", ".php", ".rb", ".swift", ".kt", ".kts", ".dart",
    ".html", ".css", ".scss", ".sql", ".sh", ".yaml", ".yml", ".json", ".toml",
    ".md", ".txt"
}
MAX_FILE_CHARS = 18000
MAX_TOTAL_CHARS = 70000


def validate_github_url(url: str) -> bool:
    url = url.strip().rstrip("/")
    return url.startswith(("https://github.com/", "http://github.com/")) and len(url.split("/")) >= 5


def clone_repository(url: str) -> str:
    if not validate_github_url(url):
        raise ValueError("Please enter a valid public GitHub repository URL.")
    target = tempfile.mkdtemp(prefix="github_code_explainer_")
    try:
        Repo.clone_from(url.strip().rstrip("/"), target, depth=1)
        return target
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        raise


def _iter_files(repo_path: str):
    root = Path(repo_path)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SOURCE_EXTENSIONS:
            yield path


def get_file_tree(repo_path: str) -> List[str]:
    files = sorted(str(p.relative_to(repo_path)).replace(os.sep, "/") for p in _iter_files(repo_path))
    return files[:300]


def extract_code(repo_path: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    total = 0
    for path in _iter_files(repo_path):
        if total >= MAX_TOTAL_CHARS:
            break
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not text.strip():
            continue
        text = text[:MAX_FILE_CHARS]
        rel = str(path.relative_to(repo_path)).replace(os.sep, "/")
        remaining = MAX_TOTAL_CHARS - total
        text = text[:remaining]
        result[rel] = text
        total += len(text)
    return result


def cleanup_repository(repo_path: str | None) -> None:
    if repo_path:
        shutil.rmtree(repo_path, ignore_errors=True)
