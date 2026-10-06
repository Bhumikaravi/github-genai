from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

import requests


IGNORED_DIRS = {
    ".git", ".github", "node_modules", "venv", ".venv", "env",
    "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build",
    "coverage", ".idea", ".vscode"
}

SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp",
    ".h", ".hpp", ".cs", ".go", ".rs", ".php", ".rb", ".swift",
    ".kt", ".kts", ".dart", ".html", ".css", ".scss", ".sql",
    ".sh", ".yaml", ".yml", ".json", ".toml", ".md", ".txt"
}

MAX_FILE_CHARS = 18000
MAX_TOTAL_CHARS = 70000


def parse_github_url(url: str):
    parsed = urlparse(url.strip().rstrip("/"))

    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError("Please enter a valid GitHub repository URL.")

    parts = [p for p in parsed.path.split("/") if p]

    if len(parts) < 2:
        raise ValueError("Please enter a valid GitHub repository URL.")

    owner = parts[0]
    repo = parts[1]

    if repo.endswith(".git"):
        repo = repo[:-4]

    return owner, repo


def validate_github_url(url: str) -> bool:
    try:
        parse_github_url(url)
        return True
    except ValueError:
        return False


def clone_repository(url: str) -> str:
    owner, repo = parse_github_url(url)

    target = tempfile.mkdtemp(prefix="github_code_explainer_")
    zip_path = os.path.join(target, "repository.zip")
    extract_path = os.path.join(target, "repo")

    os.makedirs(extract_path, exist_ok=True)

    download_url = (
        f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
    )

    response = requests.get(
        download_url,
        timeout=60,
        allow_redirects=True
    )

    if response.status_code != 200:
        download_url = (
            f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip"
        )

        response = requests.get(
            download_url,
            timeout=60,
            allow_redirects=True
        )

    if response.status_code != 200:
        shutil.rmtree(target, ignore_errors=True)
        raise RuntimeError(
            "Could not download the GitHub repository. "
            "Make sure the repository is public and the URL is correct."
        )

    with open(zip_path, "wb") as f:
        f.write(response.content)

    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            archive.extractall(extract_path)
    except zipfile.BadZipFile:
        shutil.rmtree(target, ignore_errors=True)
        raise RuntimeError("GitHub returned an invalid repository archive.")

    extracted_dirs = [
        p for p in Path(extract_path).iterdir() if p.is_dir()
    ]

    if not extracted_dirs:
        shutil.rmtree(target, ignore_errors=True)
        raise RuntimeError("The repository archive contains no files.")

    repo_root = str(extracted_dirs[0])

    try:
        os.remove(zip_path)
    except OSError:
        pass

    return repo_root


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
    files = sorted(
        str(p.relative_to(repo_path)).replace(os.sep, "/")
        for p in _iter_files(repo_path)
    )

    return files[:300]


def extract_code(repo_path: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    total = 0

    for path in _iter_files(repo_path):
        if total >= MAX_TOTAL_CHARS:
            break

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except OSError:
            continue

        if not text.strip():
            continue

        text = text[:MAX_FILE_CHARS]

        rel = str(
            path.relative_to(repo_path)
        ).replace(os.sep, "/")

        remaining = MAX_TOTAL_CHARS - total
        text = text[:remaining]

        result[rel] = text
        total += len(text)

    return result


def cleanup_repository(repo_path: str | None) -> None:
    if repo_path:
        shutil.rmtree(
            Path(repo_path).parent.parent
            if Path(repo_path).parent.name == "repo"
            else Path(repo_path),
            ignore_errors=True
        )
