from __future__ import annotations

import os
import re
import sys

import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Make Streamlit Cloud secrets available to the shared LLM service.
try:
    if "GEMINI_API_KEY" in st.secrets and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = str(st.secrets["GEMINI_API_KEY"])
except Exception:
    pass

from backend.services.llm_service import check_model, stream_explanation, using_cloud_ai
from backend.services.repo_processor import clone_repository, cleanup_repository, extract_code, get_file_tree

st.set_page_config(page_title="GitHub Code Explainer", page_icon="💻", layout="centered")

st.markdown("""
<style>
.main .block-container {max-width: 900px; padding-top: 2rem; padding-bottom: 3rem;}
.hero {padding: 2rem; border-radius: 22px; background: linear-gradient(135deg,#111827,#334155); color: white; margin-bottom: 1.5rem;}
.hero h1 {margin: 0 0 .6rem 0; font-size: 2.2rem;}
.hero p {color:#e5e7eb; font-size:1.05rem;}
.steps {display:grid; grid-template-columns:repeat(3,1fr); gap:.7rem; margin-top:1.2rem;}
.step {background:rgba(255,255,255,.1); padding:.8rem; border-radius:12px; font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

provider_text = "cloud AI" if using_cloud_ai() else "local Ollama AI"
st.markdown(f"""
<div class="hero">
<h1>💻 GitHub Code Explainer</h1>
<p>Paste a public GitHub repository and get a simple, beginner-friendly explanation.</p>
<div class="steps">
<div class="step">🔗 1. Connect to GitHub</div>
<div class="step">📂 2. Read source code</div>
<div class="step">🧠 3. Explain with AI</div>
</div>
</div>
""", unsafe_allow_html=True)

if using_cloud_ai():
    st.success("☁️ Streamlit Cloud mode: Gemini AI is connected.")
else:
    st.info("💻 Local mode: Ollama is being used. For Streamlit Cloud, add GEMINI_API_KEY in Secrets.")

url = st.text_input("GitHub Repository URL", placeholder="https://github.com/username/repository")
col1, col2 = st.columns([1, 1])
with col1:
    explain_clicked = st.button("🚀 Explain Repository", type="primary", use_container_width=True)
with col2:
    if st.button("Clear", use_container_width=True):
        st.session_state.pop("explanation", None)
        st.session_state.pop("files", None)
        st.rerun()

if explain_clicked:
    if not re.match(r"^https?://github\.com/[^/\s]+/[^/\s#?]+/?$", url.strip()):
        st.error("Please enter a valid public GitHub repository URL.")
        st.stop()

    ok, message = check_model()
    if not ok:
        st.error(message)
        st.stop()

    repo_path = None
    try:
        with st.status("Preparing repository...", expanded=True) as status:
            st.write("🔗 Cloning GitHub repository...")
            repo_path = clone_repository(url.strip())
            st.write("📂 Finding relevant source-code files...")
            files_tree = get_file_tree(repo_path)
            code_files = extract_code(repo_path)
            if not code_files:
                raise RuntimeError("No supported source-code files were found in this repository.")
            st.write(f"📄 Found {len(code_files)} relevant files.")
            st.write(f"🧠 {provider_text.title()} is analyzing the codebase...")
            placeholder = st.empty()
            chunks = []
            for chunk in stream_explanation(files_tree, code_files):
                chunks.append(chunk)
                placeholder.markdown("".join(chunks))
            explanation = "".join(chunks).strip()
            if not explanation:
                raise RuntimeError("The AI returned an empty explanation. Please try again.")
            status.update(label="Explanation ready!", state="complete", expanded=False)
        st.session_state["explanation"] = explanation
        st.session_state["files"] = files_tree
    except Exception as exc:
        st.error(f"Could not explain this repository: {exc}")
    finally:
        cleanup_repository(repo_path)

if st.session_state.get("explanation"):
    st.markdown("## 📘 Project Explanation")
    st.markdown(st.session_state["explanation"])
    files = st.session_state.get("files", [])
    with st.expander(f"📁 Files analyzed ({len(files)})"):
        st.code("\n".join(files), language="text")
    st.download_button(
        "⬇️ Download Explanation",
        data=st.session_state["explanation"],
        file_name="github_repository_explanation.md",
        mime="text/markdown",
    )

st.caption(f"Powered by GitPython + FastAPI + Streamlit + {provider_text}")
