
# Autonomous Code Review & Refactoring Agent

An AI-powered code review and refactoring agent built using Python, LangGraph, and FastAPI.

## Features

- Automated code review workflow using LangGraph
- Code linting and formatting using Flake8 and Black
- Human approval before applying changes
- Feedback-based review and retry workflow
- Rollback support
- GitHub integration using PyGithub
- REST API endpoints using FastAPI
- Demo mode when API credentials are not configured
- Unit tests using Pytest

## Tech Stack

- Python
- LangGraph
- FastAPI
- PyGithub
- OpenAI API
- Flake8
- Black
- Pytest

## Project Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd code-review-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_token
OPENAI_API_KEY=your_openai_api_key
```

These credentials are optional for demo mode.

## Run the Application

```bash
uvicorn main:app
```

Open Swagger UI:

http://127.0.0.1:8000/docs

## Run Tests

```bash
pytest
```

## API Documentation

The project includes an exported OpenAPI specification in `openapi.json`.

## Demo Mode

When API credentials are not configured, the application runs in demo mode. GitHub changes are not pushed in this mode.

## Author

Rishikesh Soni
