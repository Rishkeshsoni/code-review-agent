# Autonomous Code Review & Refactoring Agent

An automated code review and refactoring agent built using **Python, LangGraph, and FastAPI**. It analyzes Python code, detects quality issues, formats code, and applies approved changes through a Human-in-the-Loop workflow.

## Features

- LangGraph-based automated review workflow
- Code quality analysis using Flake8, Black, and Pylint
- Automated code formatting using Black
- Human-in-the-Loop approval before applying changes
- Feedback-based review and retry workflow
- Checkpointing and rollback support
- GitHub integration using PyGithub
- REST API using FastAPI
- Demo mode without OpenAI API credentials
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

1. Receive repository information and branch details through the API.
2. Fetch Python code from the target repository.
3. Analyze code using linting tools.
4. Generate formatted or refactored code.
5. Pause the workflow for human approval.
6. Accept reviewer feedback and retry when changes are rejected.
7. Commit approved changes to GitHub when the required credentials are configured.

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
│   └── test_graph.py
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

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root using `.env.example` as a reference.

Configure the following environment variables:

```env
GITHUB_TOKEN=your_github_token
OPENAI_API_KEY=your_openai_api_key
GITHUB_WEBHOOK_SECRET=your_webhook_secret
APPROVAL_API_KEY=your_approval_api_key
```

Environment variable descriptions:

- **GITHUB_TOKEN:** Used for GitHub repository access and committing approved changes.
- **OPENAI_API_KEY:** Optional. Enables AI-powered code review and semantic refactoring.
- **GITHUB_WEBHOOK_SECRET:** Used to verify GitHub webhook signatures.
- **APPROVAL_API_KEY:** Used to authenticate approval API requests.

The application supports demo mode without an OpenAI API key. GitHub integration and protected API endpoints require their respective credentials.

Never commit actual credentials or share secret values.

## Run the Application

```bash
uvicorn main:app --reload
```

**Swagger UI:**

http://127.0.0.1:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/webhooks/github` | Receives GitHub webhook events and starts the review workflow |
| POST | `/api/reviews/{thread_id}/approve` | Approves or rejects proposed changes |

## Run Tests

```bash
python -m pytest -v
```

The test suite covers:

- Python code validation and lint error detection
- Refactoring retry workflow
- Rejection and rollback handling
- Approval workflow
- API authentication
- GitHub webhook signature verification

## Human-in-the-Loop Workflow

The LangGraph workflow uses checkpointing to pause before applying changes.

A reviewer can approve proposed changes or reject them with feedback. Rejected proposals are sent back through the review workflow for another attempt, subject to the retry limit.

Approved changes can be committed to GitHub when the required credentials are configured.

## Demo Mode

The application supports demo mode without OpenAI API credentials and uses sample code to demonstrate the workflow.

Without an OpenAI API key, the fallback uses Black formatting rather than semantic AI-powered refactoring.

Without GitHub credentials, changes cannot be committed to GitHub. The webhook and approval API endpoints also require their respective security credentials.

## API Documentation

The exported OpenAPI specification is available in `openapi.json`.

## Future Improvements

- Support for additional programming languages
- More advanced code analysis and security checks
- Enhanced GitHub Pull Request integration
- Improved refactoring suggestions and test coverage

## Author

**Rishikesh Soni**

GitHub: https://github.com/Rishkeshsoni