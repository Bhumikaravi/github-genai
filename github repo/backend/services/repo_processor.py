from __future__ import annotations

import io
import os
import shutil
import tempfile
import zipfile
from typing import Dict, List, Tuple

import requests


SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".swift",
    ".kt",
    ".kts",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".sh",
    ".yaml",
    ".yml",
    ".json",
    ".xml",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

MAX_FILES = 80
MAX_FILE_SIZE = 120_000
MAX_TOTAL_CODE = 900_000


def parse_github_url(url: str) -> Tuple[str, str]:
    url = url.strip().rstrip("/")

    if url.endswith(".git"):
        url = url[:-4]

    if "github.com/" not in url:
        raise ValueError("Please enter a valid GitHub repository URL.")

    parts = url.split("github.com/", 1)[1].split("/")

    if len(parts) < 2:
        raise ValueError("GitHub URL must contain username and repository name.")

    owner = parts[0]
    repo = parts[1]

    if not owner or not repo:
        raise ValueError("Invalid GitHub repository URL.")

    return owner, repo


def validate_github_url(url: str) -> bool:
    try:
        parse_github_url(url)
        return True
    except ValueError:
        return False


def clone_repository(repo_url: str) -> str:
    """
    Downloads a public GitHub repository as a ZIP file.
    This avoids requiring GitPython or the git command on Streamlit Cloud.
    """
    owner, repo = parse_github_url(repo_url)

    temp_dir = tempfile.mkdtemp(prefix="github_explainer_")

    zip_urls = [
        f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip",
        f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip",
    ]

    last_error = None

    for zip_url in zip_urls:
        try:
            response = requests.get(zip_url, timeout=30)

            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                    archive.extractall(temp_dir)

                extracted = [
                    os.path.join(temp_dir, name)
                    for name in os.listdir(temp_dir)
                    if os.path.isdir(os.path.join(temp_dir, name))
                ]

                if extracted:
                    return extracted[0]

        except Exception as exc:
            last_error = exc

    shutil.rmtree(temp_dir, ignore_errors=True)

    if last_error:
        raise RuntimeError(f"Could not download repository: {last_error}")

    raise RuntimeError(
        "Could not download the repository. "
        "Make sure the GitHub repository is public."
    )


def _should_ignore(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")

    return any(part in IGNORED_DIRECTORIES for part in parts)


def get_file_tree(repo_path: str) -> List[str]:
    files = []

    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [
            directory
            for directory in dirs
            if directory not in IGNORED_DIRECTORIES
        ]

        for filename in filenames:
            full_path = os.path.join(root, filename)

            if _should_ignore(full_path):
                continue

            relative_path = os.path.relpath(
                full_path,
                repo_path
            ).replace("\\", "/")

            files.append(relative_path)

    return sorted(files)


def extract_code(
    repo_path: str,
    max_files: int = MAX_FILES,
    max_file_size: int = MAX_FILE_SIZE,
    max_total_code: int = MAX_TOTAL_CODE,
) -> Dict[str, str]:

    code_files: Dict[str, str] = {}
    total_size = 0

    all_files = get_file_tree(repo_path)

    preferred_names = {
        "README.md",
        "requirements.txt",
        "package.json",
        "pyproject.toml",
        "pom.xml",
        "build.gradle",
        "Dockerfile",
        "app.py",
        "main.py",
        "index.py",
    }

    all_files.sort(
        key=lambda filename: (
            0 if os.path.basename(filename) in preferred_names else 1,
            len(filename),
        )
    )

    for relative_path in all_files:

        if len(code_files) >= max_files:
            break

        extension = os.path.splitext(relative_path)[1].lower()

        basename = os.path.basename(relative_path)

        is_dockerfile = basename.lower() == "dockerfile"

        if extension not in SOURCE_EXTENSIONS and not is_dockerfile:
            continue

        full_path = os.path.join(repo_path, relative_path)

        try:
            size = os.path.getsize(full_path)
        except OSError:
            continue

        if size > max_file_size:
            continue

        if total_size + size > max_total_code:
            break

        try:
            with open(
                full_path,
                "r",
                encoding="utf-8",
                errors="ignore",
            ) as file:
                content = file.read()
        except Exception:
            continue

        if not content.strip():
            continue

        code_files[relative_path] = content
        total_size += len(content)

    return code_files


def cleanup_repository(repo_path: str) -> None:
    """
    Removes the temporary repository directory.
    """
    if not repo_path:
        return

    try:
        current = os.path.abspath(repo_path)

        if os.path.exists(current):
            shutil.rmtree(current, ignore_errors=True)

    except Exception:
        pass
