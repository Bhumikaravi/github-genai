from __future__ import annotations

import html
import os
import sys

import streamlit as st


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from backend.services.repo_processor import (
    cleanup_repository,
    clone_repository,
    extract_code,
    get_file_tree,
    validate_github_url,
)

from backend.services.llm_service import (
    check_model,
    stream_explanation,
)


st.set_page_config(
    page_title="GitHub Code Explainer",
    page_icon="🤖",
    layout="wide",
)


st.markdown(
    """
<style>

.main {
    background-color: #f7f9fc;
}

.hero {
    padding: 30px;
    border-radius: 18px;
    margin-bottom: 25px;
    background: linear-gradient(
        135deg,
        #667eea,
        #764ba2
    );
    color: white;
}

.hero h1 {
    font-size: 42px;
    margin-bottom: 8px;
}

.hero p {
    font-size: 18px;
}

.card {
    padding: 22px;
    border-radius: 15px;
    background-color: white;
    border: 1px solid #e5e7eb;
    margin-bottom: 20px;
}

.small-text {
    color: #6b7280;
}

</style>
""",
    unsafe_allow_html=True,
)


st.markdown(
    """
<div class="hero">

<h1>🤖 GitHub Code Explainer</h1>

<p>
Paste a public GitHub repository URL and let AI explain
the project, its features, technologies, files and workflow.
</p>

</div>
""",
    unsafe_allow_html=True,
)


st.markdown(
    "### 🔗 Enter GitHub Repository"
)


repo_url = st.text_input(
    "GitHub Repository URL",
    placeholder="https://github.com/username/repository",
)


explain_button = st.button(
    "🚀 Explain Repository",
    type="primary",
    use_container_width=True,
)


if explain_button:

    if not repo_url.strip():

        st.error(
            "Please enter a GitHub repository URL."
        )

        st.stop()


    if not validate_github_url(repo_url):

        st.error(
            "Please enter a valid GitHub repository URL."
        )

        st.stop()


    model_ready, model_message = check_model()

    if not model_ready:

        st.error(model_message)

        st.info(
            "Add GEMINI_API_KEY in "
            "Streamlit Cloud → Settings → Secrets."
        )

        st.stop()


    repo_path = None


    try:

        with st.status(
            "Processing repository...",
            expanded=True,
        ) as status:

            st.write(
                "📥 Downloading GitHub repository..."
            )

            repo_path = clone_repository(
                repo_url
            )


            st.write(
                "🌳 Reading repository structure..."
            )

            file_tree = get_file_tree(
                repo_path
            )


            st.write(
                f"📁 Found {len(file_tree)} files."
            )


            st.write(
                "🔍 Extracting source code..."
            )

            code_files = extract_code(
                repo_path
            )


            if not code_files:

                status.update(
                    label="No source code found",
                    state="error",
                )

                st.error(
                    "No supported source-code files "
                    "were found in this repository."
                )

                st.stop()


            st.write(
                f"🧩 Extracted {len(code_files)} source files."
            )


            st.write(
                "🤖 Asking Gemini AI to explain the project..."
            )


            status.update(
                label="Generating explanation...",
                state="running",
            )


        st.markdown(
            "## 📖 AI-Generated Explanation"
        )


        explanation_placeholder = st.empty()

        full_response = ""


        for chunk in stream_explanation(
            file_tree,
            code_files,
        ):

            full_response += chunk

            explanation_placeholder.markdown(
                full_response
            )


        if not full_response.strip():

            st.error(
                "The AI returned an empty response."
            )

        else:

            st.success(
                "Repository explanation generated successfully!"
            )


            st.download_button(
                label="⬇️ Download Explanation",
                data=full_response,
                file_name="repository_explanation.md",
                mime="text/markdown",
                use_container_width=True,
            )


            with st.expander(
                "📂 Repository Files"
            ):

                for filename in file_tree:

                    st.write(
                        f"📄 {filename}"
                    )


            with st.expander(
                "💻 Extracted Source Files"
            ):

                for filename, code in code_files.items():

                    st.markdown(
                        f"**{filename}**"
                    )

                    st.code(
                        code,
                        language="text",
                    )


    except Exception as exc:

        st.error(
            f"Could not explain this repository: {exc}"
        )

    finally:

        if repo_path:

            cleanup_repository(
                repo_path
            )


st.markdown(
    """
---

<div style="text-align:center">

<p class="small-text">
Built with Python, Streamlit and Generative AI.
</p>

</div>
""",
    unsafe_allow_html=True,
)
