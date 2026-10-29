from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "atlasforge.db"
FRONTEND_DIR = BASE_DIR / "frontend"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

app = FastAPI(title="AtlasForge API", version="1.0.0",
              description="Schema-guided AI research and knowledge navigator")


class ResearchRecord(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    summary: str = Field(default="", max_length=3000)
    claims: list[str] = Field(default_factory=list, max_length=20)
    methods: list[str] = Field(default_factory=list, max_length=20)
    limitations: list[str] = Field(default_factory=list, max_length=20)
    keywords: list[str] = Field(default_factory=list, max_length=20)
    research_questions: list[str] = Field(default_factory=list, max_length=20)
    source_text: str = Field(default="", max_length=50000)


class ExtractRequest(BaseModel):
    text: str = Field(min_length=20, max_length=50000)


def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db_connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS research_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            claims_json TEXT NOT NULL DEFAULT '[]',
            methods_json TEXT NOT NULL DEFAULT '[]',
            limitations_json TEXT NOT NULL DEFAULT '[]',
            keywords_json TEXT NOT NULL DEFAULT '[]',
            questions_json TEXT NOT NULL DEFAULT '[]',
            source_text TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_research_title ON research_records(title)")


@app.on_event("startup")
def startup():
    init_db()


def clean_list(value, limit=12):
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, str):
            item = re.sub(r"\s+", " ", item).strip(" \t\n•-*")
            if item and item not in result:
                result.append(item[:400])
        if len(result) >= limit:
            break
    return result


def fallback_extract(text: str) -> dict:
    """Local fallback so the app remains usable without an external AI key."""
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    lines = [re.sub(r"\s+", " ", line).strip(" •-*") for line in text.splitlines() if line.strip()]
    title = next((line for line in lines if len(line) > 5 and len(line) < 180), "Untitled research document")
    summary = " ".join(paragraphs[:2])[:900] or text[:900]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 35]
    lower = text.lower()
    method_terms = ("method", "approach", "model", "algorithm", "experiment", "dataset", "we use", "we propose")
    limit_terms = ("limitation", "future work", "however", "challenge", "constraint", "cannot", "not address")
    question_terms = ("?", "research question", "we ask", "whether")
    methods = [s for s in sentences if any(term in s.lower() for term in method_terms)][:6]
    limitations = [s for s in sentences if any(term in s.lower() for term in limit_terms)][:6]
    questions = [s for s in sentences if "?" in s or any(t in s.lower() for t in question_terms[1:])][:6]
    claims = [s for s in sentences if any(t in s.lower() for t in ("we find", "results show", "demonstrate", "improve", "outperform", "conclude", "our findings"))][:8]
    if not claims:
        claims = sentences[:5]
    stop = set("""about after again against all also among an and any are as at be because been before between both but by can could did do does during each few for from further had has have he her here hers him his how i if in into is it its itself just more most no nor not of off on once only or other our out over own same she should so some such than that the their them then there these they this those through to too under until up very was we were what when where which while who will with would you your""".split())
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", text.lower())
    counts = {}
    for word in words:
        if word not in stop:
            counts[word] = counts.get(word, 0) + 1
    keywords = [w for w, _ in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:10]]
    return {
        "title": title[:250], "summary": summary,
        "claims": clean_list(claims), "methods": clean_list(methods),
        "limitations": clean_list(limitations), "keywords": keywords,
        "research_questions": clean_list(questions), "source_text": text
    }


async def ai_extract(text: str) -> tuple[dict, str]:
    if not GEMINI_API_KEY:
        return fallback_extract(text), "local-fallback"
    prompt = """Extract a research document into valid JSON only. Do not invent facts. If a field is not supported by the text, return an empty string or empty array. Schema:
{"title":"string","summary":"string","claims":["string"],"methods":["string"],"limitations":["string"],"keywords":["string"],"research_questions":["string"]}
Use concise, evidence-grounded items. Document follows:
""" + text
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(url, json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
            })
            response.raise_for_status()
            body = response.json()
        raw = body["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(raw)
        data["source_text"] = text
        data["claims"] = clean_list(data.get("claims"))
        data["methods"] = clean_list(data.get("methods"))
        data["limitations"] = clean_list(data.get("limitations"))
        data["keywords"] = clean_list(data.get("keywords"))
        data["research_questions"] = clean_list(data.get("research_questions"))
        data["title"] = str(data.get("title") or "Untitled research document")[:250]
        data["summary"] = str(data.get("summary") or "")[:3000]
        return data, "gemini"
    except Exception:
        # A failed external call should not prevent a successful local workflow.
        return fallback_extract(text), "local-fallback"


def row_to_dict(row):
    return {
        "id": row["id"], "title": row["title"], "summary": row["summary"],
        "claims": json.loads(row["claims_json"]), "methods": json.loads(row["methods_json"]),
        "limitations": json.loads(row["limitations_json"]), "keywords": json.loads(row["keywords_json"]),
        "research_questions": json.loads(row["questions_json"]), "source_text": row["source_text"],
        "created_at": row["created_at"], "updated_at": row["updated_at"]
    }


def save_record(record: ResearchRecord, record_id: Optional[int] = None):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    values = (record.title, record.summary, json.dumps(record.claims), json.dumps(record.methods),
              json.dumps(record.limitations), json.dumps(record.keywords),
              json.dumps(record.research_questions), record.source_text, now)
    with db_connect() as conn:
        if record_id is None:
            cursor = conn.execute("""INSERT INTO research_records
                (title,summary,claims_json,methods_json,limitations_json,keywords_json,questions_json,source_text,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""", values + (now,))
            new_id = cursor.lastrowid
        else:
            cur = conn.execute("""UPDATE research_records SET title=?,summary=?,claims_json=?,methods_json=?,
                limitations_json=?,keywords_json=?,questions_json=?,source_text=?,updated_at=? WHERE id=?""",
                values + (record_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Research record not found")
            new_id = record_id
        row = conn.execute("SELECT * FROM research_records WHERE id=?", (new_id,)).fetchone()
        return row_to_dict(row)


@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/api/health")
def health():
    return {"status": "ok", "database": "sqlite", "ai_mode": "gemini" if GEMINI_API_KEY else "local-fallback"}


@app.post("/api/extract")
async def extract(request: ExtractRequest):
    text = request.text.strip()
    if len(text) < 20:
        raise HTTPException(status_code=422, detail="Please provide at least 20 characters of research text.")
    data, mode = await ai_extract(text)
    try:
        record = ResearchRecord(**data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="AI output did not match the required schema.") from exc
    return {"record": record.model_dump(), "ai_mode": mode, "validated": True}


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    name = (file.filename or "").lower()
    if not name.endswith((".txt", ".md")):
        raise HTTPException(status_code=415, detail="Upload a .txt or .md document. PDF parsing is not included in this minimal version.")
    content = await file.read()
    if len(content) > 1_000_000:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 1 MB.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text.") from exc
    if len(text.strip()) < 20:
        raise HTTPException(status_code=422, detail="Document must contain at least 20 characters.")
    data, mode = await ai_extract(text[:50000])
    record = ResearchRecord(**data)
    return {"record": record.model_dump(), "ai_mode": mode, "validated": True}


@app.post("/api/records")
def create_record(record: ResearchRecord):
    return {"saved": True, "record": save_record(record)}


@app.put("/api/records/{record_id}")
def update_record(record_id: int, record: ResearchRecord):
    return {"saved": True, "record": save_record(record, record_id)}


@app.get("/api/records")
def list_records(q: str = ""):
    with db_connect() as conn:
        if q.strip():
            needle = f"%{q.strip()}%"
            rows = conn.execute("""SELECT * FROM research_records WHERE title LIKE ? OR summary LIKE ?
                OR keywords_json LIKE ? ORDER BY updated_at DESC LIMIT 100""", (needle, needle, needle)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM research_records ORDER BY updated_at DESC LIMIT 100").fetchall()
    return {"records": [row_to_dict(r) for r in rows]}


@app.get("/api/records/{record_id}")
def get_record(record_id: int):
    with db_connect() as conn:
        row = conn.execute("SELECT * FROM research_records WHERE id=?", (record_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Research record not found")
    return {"record": row_to_dict(row)}


@app.delete("/api/records/{record_id}")
def delete_record(record_id: int):
    with db_connect() as conn:
        cur = conn.execute("DELETE FROM research_records WHERE id=?", (record_id,))
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Research record not found")
    return {"deleted": True, "id": record_id}
