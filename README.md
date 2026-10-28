<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=1E1E2E,4C4F69,7287FD&height=220&section=header&text=GitHub%20GenAI%20Workspace&fontSize=38&fontColor=ffffff&fontAlignY=38&desc=Generative%20AI%20Analysis%20of%20Code%20Structure%20and%20Modules&descSize=16&descAlignY=62&descAlign=50" width="100%" alt="GitHub GenAI Workspace Header Banner"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Focus-GenAI%20Code%20Intelligence-blueviolet?style=for-the-badge" alt="GenAI"/> <img src="https://img.shields.io/badge/Language-Python-3776AB?style=for-the-badge&logo=python" alt="Python"/>
</p>


## 📌 Table of Contents
- [📖 Executive Summary](#-executive-summary)
- [✨ Key Features & Capabilities](#-key-features--capabilities)
- [🏗️ System Architecture & Workflow](#️-system-architecture--workflow)
- [🛠️ Tech Stack Breakdown](#️-tech-stack-breakdown)
- [⚙️ Reproducible Quickstart & Setup](#️-reproducible-quickstart--setup)
- [📂 Project Directory Layout](#-project-directory-layout)
- [👩‍💻 Author & Contributions](#-author--contributions)

---

## 📖 Executive Summary
### Problem Statement
Analyzing nested software repositories requires recursive file filtering to eliminate binaries, node_modules, and cache files before sending context to LLMs.

### Motivation & Solution Overview
A GenAI exploration containing recursive repository processors and language model interfaces for codebase intelligence.

---

## ✨ Key Features & Capabilities
- **Recursive Tree Filtering:** Eliminates bloat and returns clean source code tokens.
- **LLM Pipeline:** Structured prompt formatting for codebase summarization.

---

## 🏗️ System Architecture & Workflow
```mermaid
flowchart LR
    Repo[Codebase Tree] --> Filter[Recursive Whitelist Filter]
    Filter --> Prompt[Context Summarizer]
    Prompt --> GenAI[GenAI LLM Integration]
```

---

## 🛠️ Tech Stack Breakdown
| Category | Technologies |
|---|---|
| **Language** | Python |
| **Tools** | GitPython, Streamlit, LLM APIs |

---

## ⚙️ Reproducible Quickstart & Setup
```bash
git clone https://github.com/Bhumikaravi/github-genai.git
cd github-genai
pip install -r "github repo/requirements.txt"
streamlit run "github repo/backend/main.py"
```

---

## 📂 Project Directory Layout
```text
github-genai/
└── github repo/
    ├── backend/
    │   ├── main.py
    │   └── services/
    │       ├── llm_service.py
    │       └── repo_processor.py
    └── requirements.txt
```

---

## 👩‍💻 Author & Contributions
Developed by **Bhumika Ravi** ([@Bhumikaravi](https://github.com/Bhumikaravi)), Bachelor of Computer Applications (BCA) at **Alliance University, Bengaluru**.

- 💻 **GitHub Profile:** [github.com/Bhumikaravi](https://github.com/Bhumikaravi)
- 🔗 **LinkedIn:** [linkedin.com/in/bhumika-ravi-b5a01b326](https://www.linkedin.com/in/bhumika-ravi-b5a01b326/)
- 📬 **Email Contact:** [bhumikaravi2006@gmail.com](mailto:bhumikaravi2006@gmail.com)

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=1E1E2E,4C4F69,7287FD&height=100&section=footer" width="100%" alt="Footer Banner"/>
</p>
