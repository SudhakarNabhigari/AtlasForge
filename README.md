AtlasForge — AI Research & Knowledge Navigator
<p align="center">
  <strong>Turn unstructured research into structured, searchable knowledge.</strong>
</p>

<p align="center">
  <a href="https://atlasforge-bhdc.onrender.com/">
    <img src="https://img.shields.io/badge/Live%20Demo-Open%20AtlasForge-8A5CF6?style=for-the-badge" alt="Live Demo">
  </a>
  <a href="https://atlasforge-bhdc.onrender.com/docs">
    <img src="https://img.shields.io/badge/API%20Docs-FastAPI-009688?style=for-the-badge" alt="API Documentation">
  </a>
</p>

🌐 Live Demo
- Live application: https://atlasforge-bhdc.onrender.com/
- Interactive API documentation: https://atlasforge-bhdc.onrender.com/docs
- API health check: https://atlasforge-bhdc.onrender.com/api/health
Note: The hosted service may take a little time to respond after a period of inactivity. Verify extraction and record saving on the live deployment before submission.

📌 About the Project
AtlasForge converts pasted research text or uploaded TXT/Markdown documents into structured research knowledge: claims, methods, limitations, keywords, a summary, and research questions. It validates the output with a Pydantic schema and stores records in SQLite.
✨ Requirements Covered
- Frontend input interface with clear structured output and validation status.
- FastAPI backend endpoints for extraction and database create/read/update/delete.
- Schema-guided AI extraction. Configure Gemini with an API key; a local rule-based fallback keeps the workflow usable without one.
- SQLite database with research records.
- Supports pasted text and .txt / .md document upload.
- Handles missing input, unsupported file types, invalid schema, missing records, and API errors.
- Review extracted fields before saving; confirm before deleting.
- Frontend and API are served from the same deployed URL, so the deployed frontend connects to its backend.
🧰 Technology Stack
- Frontend: HTML, CSS, JavaScript
- Backend: Python, FastAPI
- Validation: Pydantic
- Database: SQLite
- HTTP client: HTTPX
- Optional AI integration: Gemini API
- Deployment: Render
🚀 Run in VS Code (Windows PowerShell)
1. Extract the ZIP and open the AtlasForge folder in VS Code.
2. Open Terminal → New Terminal and run:
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload
3. Open http://127.0.0.1:8000 in your browser.
4. Paste at least 20 characters of research text or upload a .txt / .md file, click Extract Research, review the fields, and click Save to knowledge base.
5. Click Knowledge Library to search, reopen, update, or delete saved records.
If PowerShell blocks activation, use the virtual environment's Python directly after creating it:
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
🤖 Enable Gemini (Optional)
1. Copy .env.example to .env and add your Gemini API key.
2. The current setup reads environment variables directly unless you add a dotenv loader. To load .env, install python-dotenv (pip install python-dotenv) and add this near the top of backend/main.py, before environment variables are read:
from dotenv import load_dotenv
load_dotenv()
Alternatively, set the variables in PowerShell before launching the server:
$env:GEMINI_API_KEY="YOUR_API_KEY"
$env:GEMINI_MODEL="gemini-2.0-flash"
uvicorn backend.main:app --reload
Never commit a real API key. Without a key, the app uses the local fallback and displays that mode in the sidebar.
🏗️ Architecture / Workflow
Paste text / upload TXT or MD
           ↓
Frontend (HTML, CSS, JavaScript)
           ↓ POST /api/extract or /api/upload
Schema-guided extraction (Gemini API if configured; local fallback otherwise)
           ↓
Pydantic ResearchRecord validation
           ↓
User reviews / edits structured fields
           ↓ POST /api/records or PUT /api/records/{id}
FastAPI backend → SQLite (atlasforge.db)
           ↓
Frontend confirmation + searchable Knowledge Library
🗂️ Data Schema
ResearchRecord:
- title: string, required, max 250 characters
- summary: string, max 3000 characters
- claims: array of strings
- methods: array of strings
- limitations: array of strings
- keywords: array of strings
- research_questions: array of strings
- source_text: source document text
SQLite stores the structured arrays as JSON strings. The database file atlasforge.db is created automatically at startup.
🔌 API Endpoints
Method	Endpoint	Purpose
GET	/api/health	API/database mode status
POST	/api/extract	Extract structured knowledge from text
POST	/api/upload	Extract from TXT/MD upload
POST	/api/records	Create a database record
GET	/api/records	List/search saved records (?q=...)
GET	/api/records/{id}	Read one record
PUT	/api/records/{id}	Update a record
DELETE	/api/records/{id}	Delete after user confirmation


Local API docs: http://127.0.0.1:8000/docs
Deployed API docs: https://atlasforge-bhdc.onrender.com/docs
🧪 Test Cases to Demonstrate
1. Successful extraction: Paste a research abstract with more than 20 characters; check structured fields and validation badge.
2. Successful database operation: Save the result; open Knowledge Library and confirm the record appears.
3. Update operation: Reopen a record, edit its summary, and update it.
4. Missing/short input: Submit fewer than 20 characters; the app should show a clear validation message.
5. Unsupported file: Select a PDF or another unsupported file; the API should reject it with an understandable message.
6. Missing record: Request a nonexistent record ID using /api/records/999999; the API should return 404.
7. Live deployment: Open the public URL, verify /api/health, run extraction, and confirm record saving.
📝 Report Checklist
- Objective: Build a full-stack GenAI application that converts unstructured research input into structured, searchable knowledge.
- Problem statement: Research documents are long and unstructured, making claims, methods, limitations, and research questions hard to organize and search.
- Selected automation: Convert a research paper/document into structured claims, methods, limitations, and keywords; extract research questions into a searchable knowledge base.
- Technology stack: HTML, CSS, JavaScript, FastAPI, Pydantic, SQLite, HTTPX, Gemini API (optional).
- Database operation: SQLite research_records table supports create, read, update, and delete.
- Screenshots: Capture (1) input interface, (2) validated extracted output, (3) saved library record, and (4) an invalid-input message from the running app.
- Deployment URL: https://atlasforge-bhdc.onrender.com/
- Limitations: Local fallback is heuristic rather than a large language model; upload supports TXT/Markdown only; no OCR/PDF parser; extraction quality depends on source text and configured model; SQLite is suited to a small academic demonstration.
- Future improvements: PDF parsing, citation/reference parsing, vector search, evidence-linked claims, and user authentication.
🚢 Deployment Notes
The application is deployed on Render as a Python web service. The frontend is served from / by FastAPI, so the public root URL is the frontend URL to submit.
- Live application: https://atlasforge-bhdc.onrender.com/
- API documentation: https://atlasforge-bhdc.onrender.com/docs
- Health check: https://atlasforge-bhdc.onrender.com/api/health
If using Gemini, set GEMINI_API_KEY as a secret environment variable on the hosting platform. Do not place API keys in source code or commit them to GitHub.

Database persistence warning: SQLite stores data in a local database file. On hosting platforms where the service filesystem is ephemeral, records may not survive restarts or redeployments unless persistent storage is configured. Verify this behavior on the deployed service before relying on it for submission.
