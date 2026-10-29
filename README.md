# AtlasForge — AI Research & Knowledge Navigator
**Course:** CSB312 · Generative AI Foundations · CA3 Mini Project 2

AtlasForge converts pasted research text or uploaded TXT/Markdown documents into structured research knowledge: claims, methods, limitations, keywords, a summary, and research questions. It validates the output with a Pydantic schema and stores records in SQLite.

## Requirements covered
- Frontend input interface with clear structured output and validation status.
- FastAPI backend endpoints for extraction and database create/read/update/delete.
- Schema-guided AI extraction. Configure Gemini with an API key; a local rule-based fallback keeps the workflow usable without one.
- SQLite database with persistent research records.
- Supports pasted text and `.txt` / `.md` document upload.
- Handles missing input, unsupported file types, invalid schema, missing records and API errors.
- Review extracted fields before saving; confirm before deleting.
- Frontend and API are served from the same deployed URL, so the deployed frontend connects to its working backend and database.

## Run in VS Code (Windows PowerShell)
1. Extract the ZIP and open the `AtlasForge` folder in VS Code.
2. Open Terminal → PowerShell and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

3. Open **http://127.0.0.1:8000** in your browser.
4. Paste at least 20 characters of research text or upload a `.txt` / `.md` file, click **Extract research**, review the fields, and click **Save to knowledge base**.
5. Click **Knowledge library** to search, reopen, update, or delete saved records.

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload` after creating the virtual environment.

## Enable Gemini (optional)
1. Copy `.env.example` to `.env` and add your Gemini API key.
2. Install `python-dotenv` (`pip install python-dotenv`) and add `from dotenv import load_dotenv; load_dotenv()` near the top of `backend/main.py` before environment variables are read. Alternatively set the variables in the terminal before launching the server:

```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
$env:GEMINI_MODEL="gemini-2.0-flash"
uvicorn backend.main:app --reload
```

Never commit a real API key. Without a key, the app uses the local fallback and displays that mode in the sidebar.

## Architecture / workflow
```text
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
```

## Data schema
`ResearchRecord`:
- `title`: string, required, max 250 characters
- `summary`: string, max 3000 characters
- `claims`: array of strings
- `methods`: array of strings
- `limitations`: array of strings
- `keywords`: array of strings
- `research_questions`: array of strings
- `source_text`: source document text

SQLite stores the structured arrays as JSON strings. The database file `atlasforge.db` is created automatically at startup.

## API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | API/database mode status |
| POST | `/api/extract` | Extract structured knowledge from text |
| POST | `/api/upload` | Extract from TXT/MD upload |
| POST | `/api/records` | Create a database record |
| GET | `/api/records` | List/search saved records (`?q=...`) |
| GET | `/api/records/{id}` | Read one record |
| PUT | `/api/records/{id}` | Update a record |
| DELETE | `/api/records/{id}` | Delete after user confirmation |

Interactive API documentation: `http://127.0.0.1:8000/docs`

## Test cases to demonstrate
1. **Successful extraction:** paste a research abstract with more than 20 characters; check structured fields and validation badge.
2. **Successful database operation:** save the result; open Knowledge library and confirm the record appears.
3. **Update operation:** reopen a record, edit its summary, and update it.
4. **Missing/short input:** submit fewer than 20 characters; the app should show a clear validation message.
5. **Unsupported file:** select a PDF or another unsupported file; the API should reject it with an understandable message.
6. **Missing record:** request a nonexistent record ID using `/api/records/999999`; API returns 404.

## Report checklist
- **Objective:** build a full-stack GenAI application that converts unstructured research input into structured, searchable knowledge.
- **Problem statement:** research documents are long and unstructured, making claims, methods, limitations and research questions hard to organize and search.
- **Selected automation:** convert a research paper/document into structured claims, methods, limitations and keywords; extract research questions into a searchable knowledge base.
- **Technology stack:** HTML, CSS, JavaScript, FastAPI, Pydantic, SQLite, HTTPX, Gemini API (optional).
- **Database operation:** SQLite `research_records` table supports create, read, update and delete.
- **Screenshots:** capture (1) input interface, (2) validated extracted output, (3) saved library record, and (4) an invalid-input message from your running app.
- **Deployment URL:** add the actual public frontend URL after deploying. Do not submit a made-up URL.
- **Limitations:** local fallback is heuristic rather than a large language model; upload supports TXT/Markdown only; no OCR/PDF parser; extraction quality depends on source text and configured model; SQLite is suited to a small academic demonstration.
- **Future improvements:** PDF parsing, citation/reference parsing, vector search, evidence-linked claims and user authentication.

## Deployment note
Deployment is compulsory for the assignment. Deploy this FastAPI app to a host that supports Python web services and persistent storage, or use a managed database if the host filesystem is ephemeral. Set `GEMINI_API_KEY` as a secret environment variable on the host if using Gemini. The frontend is served from `/` by FastAPI, so the public root URL is the frontend URL to submit. Verify `/api/health`, extraction, and saving records on the public deployment before submission.
