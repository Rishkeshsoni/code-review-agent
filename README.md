# Autonomous Code Review & Refactoring Agent

An automated code review and refactoring agent built using Python, LangGraph, and FastAPI. The project uses a structured workflow to analyze code, identify linting issues, suggest improvements, and apply changes only after human approval.

## Features

- Automated code review workflow using LangGraph
- Code quality checks using Flake8
- Automated code formatting using Black
- Human-in-the-loop approval before applying changes
- Feedback-based review and retry workflow
- Rollback support for rejected changes
- GitHub integration using PyGithub
- REST API endpoints using FastAPI
- Demo mode without requiring API credentials
- Unit testing using Pytest

## Tech Stack

- Python
- LangGraph
- FastAPI
- PyGithub
- OpenAI API
- Flake8
- Black
- Pytest

## Project Architecture

1. Receive a repository URL and branch through the API.
2. Fetch code for review.
3. Analyze code and identify quality issues.
4. Format code using Black.
5. Pause for human approval.
6. Accept feedback and retry the review when required.
7. Apply approved changes through the configured workflow.

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

### 3. Activate the Virtual Environment

For Windows PowerShell:

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

These credentials are optional for running the application in demo mode.

## Run the Application

```bash
uvicorn main:app
```

Open Swagger UI in your browser:

http://127.0.0.1:8000/docs

## Run Tests

```bash
pytest
```

## API Documentation

The project includes an exported OpenAPI specification in `openapi.json`.

## Demo Mode

The application supports demo mode when API credentials are not configured. It uses sample code to demonstrate the review, formatting, approval, and feedback workflow.

**Note:** In demo mode, changes are not pushed to GitHub. A successful GitHub commit requires the appropriate GitHub configuration.

## Future Improvements

- More advanced AI-powered code suggestions
- Support for additional programming languages
- Improved automated refactoring
- Enhanced GitHub pull request integration

## Author

**Rishikesh Soni**

GitHub: https://github.com/Rishkeshsoni