from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from backend.services.llm_service import check_model, stream_explanation
from backend.services.repo_processor import clone_repository, cleanup_repository, extract_code, get_file_tree

app = FastAPI(title="Local GitHub Repository Code Explainer", version="1.0.0")


class ExplainRequest(BaseModel):
    github_url: HttpUrl


@app.get("/health")
def health():
    ok, message = check_model()
    return {"status": "ok" if ok else "degraded", "message": message}


@app.post("/explain")
def explain(request: ExplainRequest):
    repo_path = None
    try:
        repo_path = clone_repository(str(request.github_url))
        tree = get_file_tree(repo_path)
        files = extract_code(repo_path)
        if not files:
            raise HTTPException(status_code=400, detail="No supported source files were found.")
        chunks = list(stream_explanation(tree, files))
        return {"explanation": "".join(chunks), "files": tree}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        cleanup_repository(repo_path)
