# ExecSuite.ai - Multi-Department Collaborative Agentic Framework

**ExecSuite.ai** is a lightweight, configuration-driven multi-agent framework designed to simulate collaborative business departments (Sales outreach, Marketing campaigns, Tech development, and Executive leadership). Agents in each department "huddle in harmony," collaborating on complex tasks while reading and writing to a centralized blackboard memory space.

---

## 🌟 Supported Departments & Roles

- **C-Suite Leadership Suite**: Alice (CEO), Bob (CFO), Carol (CMO), Dave (Chief Developer)
- **Marketing Campaign Suite**: Product Marketer, Copywriter, Social Media Manager, SEO Strategist
- **Sales Outreach Suite**: Sales Director, Lead Researcher, Outreach Specialist, Customer Advocate
- **Tech Development Suite**: Product Manager, Software Architect, Developer, QA Engineer

---

## ⚙️ How It Works

1. **Shared memory blackboard**: All active agents in a department read and write to a centralized blackboard memory space.
2. **Safe Workspace Filesystem**: Agents edit files (e.g. `social_schedule.md`, `requirements.md`, code files) inside a sandboxed workspace directory `/workspace`.
3. **Flexible Collaboration Workflows**:
   - **Round-table (Collaborative)**: Agents take dynamic turns, discussing plans and refining outputs.
   - **Waterfall (Sequential)**: Agents work in structured pipeline phases, handing deliverables down the chain of command.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python), Uvicorn, Python-dotenv, Pydantic, google-genai
- **Frontend**: Vanilla Javascript (SSE client, Lucide Icons, glassmorphic CSS)
- **Quality Assurance**: Pytest, Pylint (scoring a perfect 10.00/10.00)

---

## Directory Structure

```
Agentic Organisation/
│
├── backend/
│   ├── app.py               # FastAPI server & SSE endpoint
│   ├── run.py               # Server startup entrypoint
│   ├── requirements.txt     # Python dependencies
│   ├── pytest.ini           # Pytest settings
│   ├── core/
│   │   ├── agent.py         # Base Agent class & role personas
│   │   ├── llm_wrapper.py   # Multi-provider client wrapper
│   │   ├── memory.py        # Chat log, blackboard, & safe workspace APIs
│   │   └── organization.py  # Department config & workflow orchestrators
│   └── tests/
│       └── test_core.py     # Backend unit tests
│
├── frontend/                # Dashboard files
│   ├── index.html           # HTML5 structure
│   ├── style.css            # Custom CSS styles
│   └── app.js               # EventSource connection & dynamic rendering
│
├── workspace/               # Shared output directory for agent outputs
└── .pylintrc                # Linting config
```

---

## Quick Start

### 1. Installation

Clone or download this repository, navigate to the folder, and create a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configure API Keys

Create a `.env` file inside the `backend/` directory:

```env
PORT=8000
HOST=127.0.0.1
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
```

*Note: You can also enter API keys directly in the Web UI dashboard settings.*

### 3. Launch Dashboard

Run the entrypoint script:

```bash
python backend/run.py
```

This will spin up the FastAPI server on `http://127.0.0.1:8000/` and automatically open it in your browser.
