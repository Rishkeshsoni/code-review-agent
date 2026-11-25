# Autonomous Code Review & Refactoring Agent

An automated code review and refactoring agent built using Python, LangGraph, and FastAPI. It analyzes Python code, detects quality issues, formats code, and applies approved changes through a human-in-the-loop workflow.

## Features

- LangGraph-based automated review workflow
- Code quality analysis using Flake8, Black, and Pylint
- Automated code formatting using Black
- Human-in-the-loop approval before applying changes
- Feedback-based review and retry workflow
- Checkpointing and rollback support
- GitHub integration using PyGithub
- REST API using FastAPI
- Demo mode without API credentials
- Automated tests using Pytest

## Tech Stack

- Python
- LangGraph
- FastAPI
- PyGithub
- OpenAI API
- Flake8
- Black
- Pylint
- SQLite Checkpointer
- Pytest

## Project Workflow

1. Receive repository URL and branch through the API.
2. Fetch Python code from the target repository.
3. Analyze code using linting tools.
4. Generate formatted or refactored code.
5. Pause the workflow for human approval.
6. Accept reviewer feedback and retry when changes are rejected.
7. Commit approved changes to GitHub when credentials are configured.

## Project Structure

```text
code-review-agent/
├── app/
│   ├── state.py
│   ├── nodes.py
│   ├── graph.py
│   ├── tools.py
│   └── github_client.py
├── tests/
├── configs/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── openapi.json
└── README.md
```

## Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Rishkeshsoni/code-review-agent.git
cd code-review-agent
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_token
OPENAI_API_KEY=your_openai_api_key
```

Both credentials are optional for demo mode. Never commit actual credentials.

## Run the Application

```bash
uvicorn main:app --reload
```

Swagger UI:

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/webhooks/github` | Starts a code review workflow |
| POST | `/api/reviews/{thread_id}/approve` | Approves or rejects proposed changes |

## Run Tests

```bash
python -m pytest -v
```

The test suite covers lint error detection, rejection and retry workflow, and approval workflow.

## Human-in-the-Loop Workflow

The LangGraph workflow uses checkpointing to pause before applying changes. A reviewer can approve the proposed changes or reject them with feedback. Rejected changes are sent back through the review workflow.

## Demo Mode

The application supports demo mode without API credentials and uses sample code to demonstrate the workflow.

Without an OpenAI API key, the fallback uses Black formatting rather than semantic AI-powered refactoring. Without GitHub credentials, changes are not committed to GitHub.

## API Documentation

The exported OpenAPI specification is available in `openapi.json`.

## Future Improvements

- More advanced AI-powered code suggestions
- Support for additional programming languages
- Enhanced GitHub pull request integration
- Improved refactoring and security checks

## Author

**Rishikesh Soni**

GitHub: https://github.com/Rishkeshsoni